import json

import pytest

from raspberry_pi.client import connection as connection_module
from raspberry_pi.client.connection import (
    MiniPCClient,
    MiniPCUnavailable,
    VoiceStreamClient,
)
from raspberry_pi.config import PiConfig


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise connection_module.requests.HTTPError(f"status {self.status_code}")


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.get_responses = []
        self.post_responses = []
        self.calls = []

    def get(self, url, timeout=None):
        self.calls.append(("GET", url))
        return self.get_responses.pop(0)

    def post(self, url, json=None, files=None, timeout=None):
        self.calls.append(("POST", url))
        return self.post_responses.pop(0)


def _client_with_fake_session(config: PiConfig) -> tuple[MiniPCClient, FakeSession]:
    client = MiniPCClient(config)
    fake_session = FakeSession()
    client._session = fake_session
    return client, fake_session


def test_health_returns_true_on_200():
    client, session = _client_with_fake_session(PiConfig())
    session.get_responses.append(FakeResponse(200))

    assert client.health() is True


def test_health_returns_false_on_connection_error():
    client, session = _client_with_fake_session(PiConfig())

    def _raise(*args, **kwargs):
        raise connection_module.requests.ConnectionError("down")

    session.get = _raise
    assert client.health() is False


def test_connect_parses_response_into_connect_info():
    client, session = _client_with_fake_session(PiConfig())
    session.get_responses.append(
        FakeResponse(
            200,
            {
                "session_id": "abc",
                "wake_word": "hello victoria",
                "sample_rate": 16000,
                "sample_width_bytes": 2,
                "channels": 1,
                "encoding": "pcm_s16le",
            },
        )
    )

    info = client.connect()
    assert info.session_id == "abc"
    assert info.sample_rate == 16000


def test_connect_raises_mini_pc_unavailable_on_request_error():
    client, session = _client_with_fake_session(PiConfig())

    def _raise(*args, **kwargs):
        raise connection_module.requests.ConnectionError("down")

    session.get = _raise
    with pytest.raises(MiniPCUnavailable):
        client.connect()


def test_connect_with_backoff_retries_then_succeeds():
    client, session = _client_with_fake_session(PiConfig())
    attempts = {"count": 0}

    def flaky_get(url, timeout=None):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise connection_module.requests.ConnectionError("down")
        return FakeResponse(
            200,
            {
                "session_id": "abc",
                "wake_word": "hello victoria",
                "sample_rate": 16000,
                "sample_width_bytes": 2,
                "channels": 1,
                "encoding": "pcm_s16le",
            },
        )

    session.get = flaky_get
    sleeps = []

    info = client.connect_with_backoff(0.01, 1.0, sleep_fn=sleeps.append)

    assert info.session_id == "abc"
    assert attempts["count"] == 3
    assert len(sleeps) == 2


def test_api_key_sent_as_header_when_configured():
    client = MiniPCClient(PiConfig(api_key="secret"))
    assert client._session.headers.get("X-API-Key") == "secret"


def test_voice_stream_client_url_includes_session_and_api_key():
    config = PiConfig(mini_pc_url="http://10.0.0.5:8000", api_key="secret")
    stream_client = VoiceStreamClient(config, "session-123")

    url = stream_client._url()
    assert url == "ws://10.0.0.5:8000/voice/stream?session_id=session-123&api_key=secret"


def test_voice_stream_client_connect_with_backoff_retries(monkeypatch):
    config = PiConfig(reconnect_initial_delay_seconds=0.01, reconnect_max_delay_seconds=0.05)
    stream_client = VoiceStreamClient(config, "session-123")

    attempts = {"count": 0}

    class FakeConnection:
        def recv(self, timeout=None):
            return json.dumps({"event": "connected"})

    def flaky_connect(url, open_timeout=10, ping_interval=20):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise OSError("connection refused")
        return FakeConnection()

    monkeypatch.setattr(connection_module, "connect", flaky_connect)

    sleeps = []
    connection = stream_client.connect_with_backoff(sleep_fn=sleeps.append)

    assert attempts["count"] == 2
    assert len(sleeps) == 1
    assert isinstance(connection, FakeConnection)
