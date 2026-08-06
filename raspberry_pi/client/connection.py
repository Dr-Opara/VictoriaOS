"""HTTP + WebSocket client for talking to the Mini PC (Victoria Brain).

The Raspberry Pi never calls OpenAI or any GPT endpoint directly - every
capability here is a thin wrapper around the Mini PC's ``/voice/*`` API.
Uses the synchronous websocket client so the voice node can stay a single
blocking loop (matching the sounddevice callback/queue model) rather than
mixing asyncio with thread-based audio I/O.
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import requests
import websockets
from websockets.sync.client import ClientConnection, connect

from raspberry_pi.config import PiConfig
from raspberry_pi.logging_config import get_logger

logger = get_logger()


class MiniPCUnavailable(RuntimeError):
    """Raised when the Mini PC cannot be reached at all."""


class ProtocolError(RuntimeError):
    """Raised when the Mini PC sends a message that violates the voice-stream protocol."""


@dataclass
class ConnectInfo:
    session_id: str
    wake_word: str
    sample_rate: int
    sample_width_bytes: int
    channels: int
    encoding: str


class MiniPCClient:
    """REST client for the Mini PC's non-streaming voice endpoints."""

    def __init__(self, config: PiConfig) -> None:
        self.config = config
        self._session = requests.Session()
        if config.api_key:
            self._session.headers["X-API-Key"] = config.api_key

    def _url(self, path: str) -> str:
        return f"{self.config.mini_pc_url.rstrip('/')}{path}"

    def health(self, timeout: float = 5.0) -> bool:
        """Return ``True`` if the Mini PC responds healthy."""
        try:
            response = self._session.get(self._url("/health"), timeout=timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def connect(self, timeout: float = 5.0) -> ConnectInfo:
        """Handshake with the Mini PC and get streaming parameters."""
        try:
            response = self._session.get(self._url("/voice/connect"), timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as error:
            raise MiniPCUnavailable(f"Could not reach Mini PC: {error}") from error

        data = response.json()
        return ConnectInfo(**data)

    def connect_with_backoff(
        self, initial_delay: float, max_delay: float, sleep_fn=time.sleep
    ) -> ConnectInfo:
        """Handshake with the Mini PC, retrying with exponential backoff."""
        delay = initial_delay
        while True:
            try:
                return self.connect()
            except MiniPCUnavailable as error:
                logger.warning("Mini PC unavailable (%s); retrying in %.1fs", error, delay)
                sleep_fn(delay)
                delay = min(delay * 2, max_delay)

    def transcribe(self, audio: bytes, timeout: float = 30.0) -> str:
        """Transcribe a complete audio clip via the Mini PC."""
        response = self._session.post(
            self._url("/voice/transcribe"),
            files={"audio": ("clip.wav", audio, "audio/wav")},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()["transcript"]

    def respond(
        self, text: str, session_id: str, audio_format: str = "wav", timeout: float = 30.0
    ) -> dict[str, Any]:
        """Send transcribed text to Victoria and get her spoken reply."""
        response = self._session.post(
            self._url("/voice/respond"),
            json={
                "text": text,
                "session_id": session_id,
                "include_audio": True,
                "audio_format": audio_format,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()


class VoiceStream:
    """One connected ``/voice/stream`` session."""

    def __init__(self, connection: ClientConnection) -> None:
        self._ws = connection

    def send_audio(self, pcm_chunk: bytes) -> None:
        self._ws.send(pcm_chunk)

    def end_of_turn(self) -> None:
        self._ws.send(json.dumps({"event": "end_of_turn"}))

    def ping(self) -> None:
        self._ws.send(json.dumps({"event": "ping"}))

    def receive(self, timeout: float | None = None) -> dict[str, Any] | bytes:
        """Receive one message: a parsed JSON dict, or raw audio bytes."""
        message = self._ws.recv(timeout=timeout)
        if isinstance(message, bytes):
            return message
        return json.loads(message)

    def receive_turn_result(self, timeout: float = 30.0) -> tuple[dict[str, Any], bytes | None]:
        """Receive a ``result`` JSON message and the audio that may follow it.

        Raises :class:`ProtocolError` if the server sends binary audio
        where a JSON result was expected - a protocol violation that should
        surface clearly rather than crashing on an attribute access deeper
        in the caller.
        """
        result = self.receive(timeout=timeout)
        while isinstance(result, dict) and result.get("event") == "pong":
            result = self.receive(timeout=timeout)

        if not isinstance(result, dict):
            raise ProtocolError("Expected a JSON result message but received binary audio.")

        audio: bytes | None = None
        if result.get("status") == "awake":
            maybe_audio = self.receive(timeout=timeout)
            if isinstance(maybe_audio, bytes):
                audio = maybe_audio

        return result, audio


class VoiceStreamClient:
    """Connects to ``/voice/stream`` with automatic reconnect-with-backoff."""

    def __init__(self, config: PiConfig, session_id: str) -> None:
        self.config = config
        self.session_id = session_id

    def _url(self) -> str:
        base = self.config.mini_pc_url.rstrip("/").replace("http://", "ws://").replace(
            "https://", "wss://"
        )
        url = f"{base}/voice/stream?session_id={self.session_id}"
        if self.config.api_key:
            url += f"&api_key={self.config.api_key}"
        return url

    def connect_with_backoff(self, sleep_fn=time.sleep) -> ClientConnection:
        """Connect, retrying with exponential backoff until it succeeds."""
        delay = self.config.reconnect_initial_delay_seconds
        while True:
            try:
                connection = connect(self._url(), open_timeout=10, ping_interval=20)
                greeting = connection.recv(timeout=10)
                logger.info("Voice stream connected: %s", greeting)
                return connection
            except (OSError, websockets.WebSocketException) as error:
                logger.warning(
                    "Voice stream connect failed (%s); retrying in %.1fs", error, delay
                )
                sleep_fn(delay)
                delay = min(delay * 2, self.config.reconnect_max_delay_seconds)

    @contextmanager
    def connected(self):
        connection = self.connect_with_backoff()
        try:
            yield VoiceStream(connection)
        finally:
            connection.close()
