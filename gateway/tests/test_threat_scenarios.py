from tests.threat_scenarios import ThreatScenarioRunner


def test_threat_scenarios_detect(tmp_path):
    runner = ThreatScenarioRunner(db_path=str(tmp_path / 'threat.db'))
    results = runner.run()

    assert len(results) >= 6
    for result in results:
        assert result.actual
        assert result.latency_ms >= 0
        assert result.detection_success is True
