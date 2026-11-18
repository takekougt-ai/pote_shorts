"""
Run this locally ONCE to obtain a TikTok OAuth access/refresh token pair for
the Content Posting API (video.publish scope).

Prerequisites:
  - A TikTok for Developers app with the "Content Posting API" product
    added and the video.publish scope enabled.
  - A redirect URI registered on the app (any HTTPS URL you control, even
    one that just shows a blank page, works).

Usage:
    python scripts/authorize_tiktok.py \
        --client-key YOUR_CLIENT_KEY \
        --client-secret YOUR_CLIENT_SECRET \
        --redirect-uri https://your-registered-redirect-uri

Steps:
  1. The script prints an authorization URL. Open it in a browser, log in,
     and approve access.
  2. TikTok redirects to your redirect URI with a `?code=...` query
     parameter (the page itself may show an error/blank screen -- that's
     fine, you only need the URL from the address bar).
  3. Paste the FULL redirected URL back into this script when prompted.
"""

import argparse
import urllib.parse

import requests

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-key", required=True)
    parser.add_argument("--client-secret", required=True)
    parser.add_argument("--redirect-uri", required=True)
    args = parser.parse_args()

    params = {
        "client_key": args.client_key,
        "response_type": "code",
        "scope": "video.publish",
        "redirect_uri": args.redirect_uri,
        "state": "pote_shorts_setup",
    }
    print("Open this URL in your browser and approve access:\n")
    print(f"{AUTH_URL}?{urllib.parse.urlencode(params)}\n")

    redirected_url = input("Paste the full redirected URL here: ").strip()
    query = urllib.parse.urlparse(redirected_url).query
    code = urllib.parse.parse_qs(query).get("code", [None])[0]
    if not code:
        raise SystemExit("Could not find a 'code' parameter in the redirected URL.")

    resp = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": args.client_key,
            "client_secret": args.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": args.redirect_uri,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    print("\n=== Save these as GitHub Actions secrets ===")
    print(f"TIKTOK_CLIENT_KEY={args.client_key}")
    print(f"TIKTOK_CLIENT_SECRET={args.client_secret}")
    print(f"TIKTOK_REFRESH_TOKEN={data['refresh_token']}")
    print(f"\n(access_token, valid ~24h, not needed as a secret: {data['access_token']})")


if __name__ == "__main__":
    main()
