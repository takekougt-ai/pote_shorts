import os
import sys
import tempfile
import traceback
from datetime import datetime, timezone

from . import config
from .drive_client import DriveClient
from .state import StateStore, shuffled_order
from .tiktok_client import TikTokClient
from .youtube_client import YouTubeClient

MAX_SKIP_ATTEMPTS = 50
MAX_HISTORY_ENTRIES = 500


def build_caption(file_name: str) -> tuple[str, str]:
    base = os.path.splitext(file_name)[0]
    caption = base
    if config.HASHTAGS:
        caption = f"{caption}\n\n{config.HASHTAGS}"
    return config.VIDEO_TITLE[:100], caption


def pick_next_file(state, file_map: dict, store: StateStore) -> str:
    """Return the next video's Drive file id, rebuilding/reshuffling the
    queue when a cycle completes and pruning videos that no longer exist."""
    attempts = 0
    while attempts < MAX_SKIP_ATTEMPTS:
        if not state.order or state.cursor >= len(state.order):
            state.order = shuffled_order(list(file_map.keys()))
            state.cursor = 0
            state.cycle += 1
            store.save(state)
            print(f"Starting cycle {state.cycle} with {len(state.order)} videos (freshly shuffled).")

        file_id = state.order[state.cursor]
        if file_id in file_map:
            return file_id

        print(f"Video {file_id} no longer exists in the Drive folder; skipping it.")
        del state.order[state.cursor]
        store.save(state)
        attempts += 1

    raise RuntimeError("Could not find a valid video to post after multiple attempts.")


def main() -> int:
    store = StateStore(config.STATE_FILE_PATH)
    state = store.load()

    drive = DriveClient()
    files = drive.list_videos(config.DRIVE_FOLDER_ID)
    if not files:
        print("Drive folder contains no video files; nothing to post today.")
        return 0
    file_map = {f["id"]: f for f in files}

    if state.pending:
        file_id = state.pending["file_id"]
        if file_id not in file_map:
            print(f"Pending video {file_id} was removed from Drive; dropping it and picking a new one.")
            if state.order and state.cursor < len(state.order) and state.order[state.cursor] == file_id:
                del state.order[state.cursor]
            state.pending = None
            store.save(state)
            file_id = pick_next_file(state, file_map, store)
    else:
        file_id = pick_next_file(state, file_map, store)

    file_info = file_map[file_id]

    pending = state.pending or {
        "file_id": file_id,
        "file_name": file_info["name"],
        "youtube_done": False,
        "tiktok_done": False,
        "youtube_video_id": None,
        "tiktok_publish_id": None,
    }
    state.pending = pending
    store.save(state)

    title, caption = build_caption(file_info["name"])

    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = os.path.join(tmpdir, file_info["name"])
        print(f"Downloading '{file_info['name']}' from Google Drive...")
        drive.download(file_id, local_path)

        if not pending["youtube_done"]:
            print("Uploading to YouTube Shorts...")
            try:
                youtube = YouTubeClient()
                pending["youtube_video_id"] = youtube.upload_short(local_path, title=title, description=caption)
                pending["youtube_done"] = True
                store.save(state)
                print(f"YouTube upload complete: {pending['youtube_video_id']}")
            except Exception:
                traceback.print_exc()
                store.save(state)
                print("YouTube upload failed. Will retry the same video on the next run.")
                return 1

        if not config.TIKTOK_ENABLED:
            print("TikTok is not configured; skipping TikTok upload.")
            pending["tiktok_done"] = True
            store.save(state)
        elif not pending["tiktok_done"]:
            print("Uploading to TikTok...")
            try:
                tiktok = TikTokClient()
                pending["tiktok_publish_id"] = tiktok.post_video(local_path, caption=caption)
                pending["tiktok_done"] = True
                store.save(state)
                print(f"TikTok upload complete: {pending['tiktok_publish_id']}")
            except Exception:
                traceback.print_exc()
                store.save(state)
                print("TikTok upload failed. Will retry the same video on the next run.")
                return 1

    state.history.append(
        {
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "cycle": state.cycle,
            "file_id": file_id,
            "file_name": file_info["name"],
            "youtube_video_id": pending["youtube_video_id"],
            "tiktok_publish_id": pending["tiktok_publish_id"],
        }
    )
    state.history = state.history[-MAX_HISTORY_ENTRIES:]
    state.cursor += 1
    state.pending = None
    store.save(state)

    print(
        f"Posted '{file_info['name']}' (cycle {state.cycle}, "
        f"{state.cursor}/{len(state.order)} in this cycle)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
