"""
Run this locally ONCE PER ACCOUNT to obtain a Google OAuth refresh token.

The Drive folder and the YouTube channel can belong to two different
Google accounts. Run this script twice with --target drive / --target
youtube, logging in with the matching account each time (use an
incognito/private window, or log out first, to switch accounts).

Prerequisites:
  - A Google Cloud project with the "Google Drive API" and
    "YouTube Data API v3" enabled.
  - An OAuth 2.0 Client ID of type "Desktop app" created for that project
    (the SAME client_id/client_secret is reused for both accounts).
  - Both Google accounts added as test users on the OAuth consent screen
    (required while the app is in "Testing" publishing status).

Usage:
    python scripts/authorize_google.py \
        --client-id YOUR_CLIENT_ID \
        --client-secret YOUR_CLIENT_SECRET \
        --target drive

Steps:
  1. The script prints an authorization URL. Open it in a browser, log in
     with the matching account, and approve access.
  2. The browser is redirected to http://localhost/... which will show a
     "connection refused" / "site can't be reached" error page -- that is
     expected, since nothing is actually listening there. You only need
     the URL from the browser's address bar.
  3. Paste that FULL address-bar URL back into this script when prompted.
"""

import argparse
import os

# The redirect URI below is http:// (not https://), which the underlying
# oauthlib would otherwise reject as an insecure transport. This is safe
# here because the "connection" never actually leaves the local machine;
# we only read the code out of the redirected URL, we never send it there.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

from google_auth_oauthlib.flow import Flow  # noqa: E402

SCOPES_BY_TARGET = {
    "drive": ["https://www.googleapis.com/auth/drive.readonly"],
    "youtube": ["https://www.googleapis.com/auth/youtube.upload"],
}
SECRET_NAME_BY_TARGET = {
    "drive": "DRIVE_REFRESH_TOKEN",
    "youtube": "YOUTUBE_REFRESH_TOKEN",
}
REDIRECT_URI = "http://localhost"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", required=True)
    parser.add_argument(
        "--target",
        choices=["drive", "youtube"],
        required=True,
        help="Which account you're about to log in with: the Drive folder owner or the YouTube channel owner.",
    )
    args = parser.parse_args()

    client_config = {
        "installed": {
            "client_id": args.client_id,
            "client_secret": args.client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES_BY_TARGET[args.target], redirect_uri=REDIRECT_URI)
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent", include_granted_scopes="true")

    print(f"\n[{args.target}] Open this URL in your browser and approve access:\n")
    print(auth_url)
    print(
        "\nAfter approving, the browser will land on a 'connection refused' "
        "page at http://localhost/... -- that's expected. Copy the FULL "
        "URL from the address bar."
    )

    redirected_url = input("\nPaste the full redirected URL here: ").strip()
    flow.fetch_token(authorization_response=redirected_url)
    creds = flow.credentials

    secret_name = SECRET_NAME_BY_TARGET[args.target]
    print(f"\n=== Save these as GitHub Actions secrets ({args.target} account) ===")
    print(f"GOOGLE_CLIENT_ID={args.client_id}")
    print(f"GOOGLE_CLIENT_SECRET={args.client_secret}")
    print(f"{secret_name}={creds.refresh_token}")


if __name__ == "__main__":
    main()
