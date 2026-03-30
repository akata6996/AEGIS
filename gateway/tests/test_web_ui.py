from fastapi.testclient import TestClient

from app import main as main_module


class _Noop:
    def start(self):
        return None

    def stop(self):
        return None


def test_ui_page_renders(monkeypatch):
    monkeypatch.setattr(main_module, 'mqtt_service', _Noop())
    monkeypatch.setattr(main_module, 'pipeline_worker', _Noop())
    with TestClient(main_module.app) as client:
        response = client.get('/api/v1/ui')
        assert response.status_code == 200
        assert 'AEGIS Operator Console' in response.text


def test_root_redirects_to_ui(monkeypatch):
    monkeypatch.setattr(main_module, 'mqtt_service', _Noop())
    monkeypatch.setattr(main_module, 'pipeline_worker', _Noop())
    with TestClient(main_module.app) as client:
        response = client.get('/', follow_redirects=False)
        assert response.status_code in (302, 307)
        assert response.headers['location'] == '/api/v1/ui'
