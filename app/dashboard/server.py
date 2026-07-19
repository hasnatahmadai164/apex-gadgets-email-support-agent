import secrets

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.dashboard.stats import get_today_stats
from app.db.session import get_session

app = FastAPI(title="Apex Gadgets Support Dashboard")
app.mount("/static", StaticFiles(directory="app/dashboard/static"), name="static")
templates = Jinja2Templates(directory="app/dashboard/templates")

security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    settings = get_settings()
    expected_password = settings.dashboard_admin_password or ""

    correct_username = secrets.compare_digest(credentials.username, settings.dashboard_admin_username)
    correct_password = bool(expected_password) and secrets.compare_digest(
        credentials.password, expected_password
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/")
def dashboard_page(request: Request, _: str = Depends(require_admin)):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/stats")
def stats_endpoint(_: str = Depends(require_admin)):
    session = next(get_session())
    try:
        return get_today_stats(session)
    finally:
        session.close()


@app.get("/health")
def health_check():
    return {"status": "ok"}
