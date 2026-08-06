from raspberry_pi.health.monitor import ComponentStatus, HealthMonitor, snapshot
from raspberry_pi.config import PiConfig


class FakeMiniPCClient:
    def __init__(self, healthy: bool):
        self._healthy = healthy

    def health(self) -> bool:
        return self._healthy


def test_snapshot_reports_mini_pc_ok(monkeypatch):
    monkeypatch.setattr("raspberry_pi.health.monitor.check_microphone", lambda: ComponentStatus.OK)
    monkeypatch.setattr("raspberry_pi.health.monitor.check_speaker", lambda: ComponentStatus.OK)

    result = snapshot(FakeMiniPCClient(healthy=True))

    assert result.mini_pc == ComponentStatus.OK
    assert result.healthy is True


def test_snapshot_reports_mini_pc_unavailable(monkeypatch):
    monkeypatch.setattr("raspberry_pi.health.monitor.check_microphone", lambda: ComponentStatus.OK)
    monkeypatch.setattr("raspberry_pi.health.monitor.check_speaker", lambda: ComponentStatus.OK)

    result = snapshot(FakeMiniPCClient(healthy=False))

    assert result.mini_pc == ComponentStatus.UNAVAILABLE
    assert result.healthy is False


def test_health_monitor_start_stop_runs_without_error(monkeypatch):
    monkeypatch.setattr("raspberry_pi.health.monitor.check_microphone", lambda: ComponentStatus.OK)
    monkeypatch.setattr("raspberry_pi.health.monitor.check_speaker", lambda: ComponentStatus.OK)

    config = PiConfig(heartbeat_interval_seconds=0.05)
    monitor = HealthMonitor(config, FakeMiniPCClient(healthy=True))

    monitor.start()
    monitor.stop()
