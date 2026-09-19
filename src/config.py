import os


def _env(name: str, default: str | None = None, required: bool = False) -> str | None:
    # Treat an empty string the same as "unset" so that GitHub Actions repo
    # variables left unconfigured (which resolve to "") still fall back to
    # the default instead of clobbering it.
    value = os.environ.get(name) or default
    if required and not value:
        raise RuntimeError(f"Required environment variable {name} is not set.")
    return value


DRIVE_FOLDER_ID = _env("DRIVE_FOLDER_ID", required=True)

# A single OAuth client (client_id/secret) is reused to authorize two
# different Google accounts: one that owns the Drive folder, and one that
# owns the YouTube channel. Each account gets its own refresh token.
GOOGLE_CLIENT_ID = _env("GOOGLE_CLIENT_ID", required=True)
GOOGLE_CLIENT_SECRET = _env("GOOGLE_CLIENT_SECRET", required=True)
DRIVE_REFRESH_TOKEN = _env("DRIVE_REFRESH_TOKEN", required=True)
YOUTUBE_REFRESH_TOKEN = _env("YOUTUBE_REFRESH_TOKEN", required=True)

# TikTok posting is optional. Leave these three unset to post to YouTube
# Shorts only; the bot will skip the TikTok step entirely.
TIKTOK_CLIENT_KEY = _env("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = _env("TIKTOK_CLIENT_SECRET")
TIKTOK_REFRESH_TOKEN = _env("TIKTOK_REFRESH_TOKEN")
TIKTOK_ENABLED = bool(TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET and TIKTOK_REFRESH_TOKEN)
# Unaudited TikTok apps may only post as SELF_ONLY (private/draft). Once the
# app passes TikTok's Content Posting API audit, this can be changed to
# PUBLIC_TO_EVERYONE / MUTUAL_FOLLOW_FRIENDS / FOLLOWER_OF_CREATOR.
TIKTOK_PRIVACY_LEVEL = _env("TIKTOK_PRIVACY_LEVEL", default="SELF_ONLY")

VIDEO_TITLE = _env("VIDEO_TITLE", default="ぽてぽてアーカイブ劇場")

YOUTUBE_PRIVACY_STATUS = _env("YOUTUBE_PRIVACY_STATUS", default="public")
YOUTUBE_CATEGORY_ID = _env("YOUTUBE_CATEGORY_ID", default="22")
YOUTUBE_TAGS = [t.strip() for t in (_env("YOUTUBE_TAGS", default="") or "").split(",") if t.strip()]

HASHTAGS = _env("HASHTAGS", default="")

STATE_FILE_PATH = _env("STATE_FILE_PATH", default="state/queue_state.json")
