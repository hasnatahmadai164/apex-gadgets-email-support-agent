import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials

from app.core.config import get_settings
from app.dashboard.server import require_admin


def test_require_admin_accepts_correct_credentials(monkeypatch):
    monkeypatch.setenv("DASHBOARD_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DASHBOARD_ADMIN_PASSWORD", "secret")
    get_settings.cache_clear()

    credentials = HTTPBasicCredentials(username="admin", password="secret")
    assert require_admin(credentials) == "admin"


def test_require_admin_rejects_wrong_password(monkeypatch):
    monkeypatch.setenv("DASHBOARD_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DASHBOARD_ADMIN_PASSWORD", "secret")
    get_settings.cache_clear()

    credentials = HTTPBasicCredentials(username="admin", password="wrong")
    with pytest.raises(HTTPException):
        require_admin(credentials)


def test_require_admin_rejects_when_no_password_configured(monkeypatch):
    monkeypatch.setenv("DASHBOARD_ADMIN_USERNAME", "admin")
    monkeypatch.delenv("DASHBOARD_ADMIN_PASSWORD", raising=False)
    get_settings.cache_clear()

    credentials = HTTPBasicCredentials(username="admin", password="")
    with pytest.raises(HTTPException):
        require_admin(credentials)
