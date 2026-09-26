from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from . import config

# The Drive folder and the YouTube channel may belong to different Google
# accounts, so each gets its own refresh token (obtained by running
# scripts/authorize_google.py once per account). Both accounts can share the
# same OAuth client (client_id/secret) from the same Cloud project.
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _build_credentials(refresh_token: str, scopes: list[str]) -> Credentials:
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=scopes,
    )
    creds.refresh(Request())
    return creds


def get_drive_credentials() -> Credentials:
    return _build_credentials(config.DRIVE_REFRESH_TOKEN, DRIVE_SCOPES)


def get_youtube_credentials() -> Credentials:
    return _build_credentials(config.YOUTUBE_REFRESH_TOKEN, YOUTUBE_SCOPES)
