from google_auth_oauthlib.flow import InstalledAppFlow

from app.core.config import get_settings
from app.tools.gmail_tools import SCOPES


def main():
    settings = get_settings()
    client_config = {
        "installed": {
            "client_id": settings.gmail_client_id,
            "client_secret": settings.gmail_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    credentials = flow.run_local_server(port=0)

    print("Refresh token, copy this into GMAIL_REFRESH_TOKEN in .env:")
    print(credentials.refresh_token)


if __name__ == "__main__":
    main()
