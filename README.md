# pote_shorts

Google Drive に保存したショート動画を、毎日1本ずつ **TikTok** と **YouTube Shorts** に自動投稿する Bot です。

## 仕組み

- 投稿順序はサイクル(1週間 = 動画本数ぶんの投稿)の開始時にランダムにシャッフルして決定します。
- そのサイクルが最後まで終わったら(2週目、3週目…)、その時点の Drive フォルダの中身を元に**再度ランダムシャッフルして**次のサイクルを開始します。動画を追加/削除していればそれも反映されます。
- 投稿の進捗(現在のサイクル番号・シャッフル順・カーソル位置・投稿履歴)は `state/queue_state.json` に保存し、GitHub Actions の実行のたびにリポジトリへコミットして永続化します。
- 毎日 GitHub Actions の scheduled workflow (`.github/workflows/daily_post.yml`) が起動し、キューの次の動画を Drive からダウンロードして YouTube → TikTok の順にアップロードします。
- どちらかのプラットフォームへのアップロードが失敗した場合、キューは進めずに同じ動画を次回実行時に再試行します(成功済みのプラットフォームには再投稿しません)。

## セットアップ手順

### 1. Google Drive フォルダを準備

ショート動画(mp4など、`video/*` mimeType)を1つのフォルダにまとめます。フォルダURLから `DRIVE_FOLDER_ID` を控えます。

```
https://drive.google.com/drive/folders/<この部分がDRIVE_FOLDER_ID>
```

### 2. Google Cloud の準備

Drive フォルダの所有アカウントと YouTube チャンネルの所有アカウントが異なる場合でも、**同じ OAuth クライアント (client_id/secret) を使い回して、アカウントごとに別々のリフレッシュトークンを発行**すれば問題ありません。

1. Google Cloud Console でプロジェクトを作成し、**Google Drive API** と **YouTube Data API v3** を有効化します。
2. 「認証情報」から OAuth クライアントID (種類: デスクトップアプリ) を作成し、client_id / client_secret を控えます。
3. OAuth 同意画面の「テストユーザー」に、**Drive フォルダを持つ Google アカウント** と **YouTube チャンネルを持つ Google アカウント** の両方を追加します(アプリが「テスト」ステータスのままだと、テストユーザー登録されたアカウントしかログインできません)。
4. ローカル環境で以下を実行し、**Drive アカウント用**のリフレッシュトークンを取得します。

```bash
pip install -r requirements.txt
python scripts/authorize_google.py \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET \
  --target drive
```

実行すると認証用URLが表示されるので、ブラウザで開いて **Drive フォルダを持つアカウント**でログイン・許可してください。許可後、ブラウザは `http://localhost/...` へ遷移し「このサイトにアクセスできません」というエラーページになりますが、**これは正常な動作です**(ローカルに何も待ち受けていないだけで、必要なのはこのURL自体です)。そのアドレスバーのURLを丸ごとコピーし、ターミナルの `Paste the full redirected URL here:` のプロンプトに貼り付けてEnterしてください。

5. 続けて、**別ブラウザ/シークレットウィンドウ**などで一旦ログアウトした状態にしてから、以下を実行し**YouTube アカウント用**のリフレッシュトークンを取得します(同様にYouTubeチャンネルを持つアカウントでログイン・許可し、リダイレクト先のURLを貼り付けます)。

```bash
python scripts/authorize_google.py \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET \
  --target youtube
```

それぞれ表示された `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `DRIVE_REFRESH_TOKEN` / `YOUTUBE_REFRESH_TOKEN` を後で GitHub Secrets に登録します(client_id/secret は共通の値です)。

### 3. TikTok Developers の準備(任意)

TikTokへの投稿は任意です。`TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` / `TIKTOK_REFRESH_TOKEN` の3つのSecretsを未設定のままにしておけば、Botは自動的にTikTok投稿をスキップし、YouTube Shortsのみに投稿します。後からTikTok連携を追加したくなった場合は、以下の手順でSecretsを登録すれば有効になります。

1. [TikTok for Developers](https://developers.tiktok.com/) でアプリを作成し、**Content Posting API** プロダクトを追加、`video.publish` スコープを有効化します。
2. リダイレクトURI(自分が管理するHTTPSのURLで構いません)を登録します。
3. ローカル環境で以下を実行し、認可コードを交換してトークンを取得します。

```bash
python scripts/authorize_tiktok.py \
  --client-key YOUR_CLIENT_KEY \
  --client-secret YOUR_CLIENT_SECRET \
  --redirect-uri https://your-registered-redirect-uri
```

表示された値を控えます。

> **重要:** TikTok の Content Posting API は、アプリが TikTok の審査(Audit)を通過するまで **公開投稿ができず、投稿は投稿者本人のみ閲覧可能(`SELF_ONLY`)** になります。審査完了後に `TIKTOK_PRIVACY_LEVEL` を `PUBLIC_TO_EVERYONE` 等に変更してください。

### 4. GitHub Secrets / Variables を登録

リポジトリの Settings → Secrets and variables → Actions で以下を設定します。

**Secrets(必須・機密情報)**

| 名前 | 内容 |
|---|---|
| `DRIVE_FOLDER_ID` | 手順1で控えたフォルダID |
| `GOOGLE_CLIENT_ID` | 手順2 |
| `GOOGLE_CLIENT_SECRET` | 手順2 |
| `DRIVE_REFRESH_TOKEN` | 手順2 (`--target drive` で取得) |
| `YOUTUBE_REFRESH_TOKEN` | 手順2 (`--target youtube` で取得) |
| `TIKTOK_CLIENT_KEY` | 手順3(任意。未設定ならTikTok投稿をスキップ) |
| `TIKTOK_CLIENT_SECRET` | 手順3(任意。未設定ならTikTok投稿をスキップ) |
| `TIKTOK_REFRESH_TOKEN` | 手順3(任意。未設定ならTikTok投稿をスキップ) |

**Variables(任意・未設定ならデフォルト値を使用)**

| 名前 | デフォルト | 内容 |
|---|---|---|
| `VIDEO_TITLE` | `POTE daily shorts` | YouTubeのタイトルとして全動画共通で使う文字列 |
| `TIKTOK_PRIVACY_LEVEL` | `SELF_ONLY` | TikTok投稿の公開範囲 |
| `YOUTUBE_PRIVACY_STATUS` | `public` | YouTube投稿の公開範囲 (`public`/`unlisted`/`private`) |
| `YOUTUBE_CATEGORY_ID` | `22` | YouTubeカテゴリID |
| `YOUTUBE_TAGS` | (空) | カンマ区切りのタグ |
| `HASHTAGS` | (空) | 両プラットフォームの説明欄末尾に付けるハッシュタグ等 |

### 5. ワークフローを有効化

- `.github/workflows/daily_post.yml` は毎日 21:00 UTC (= 06:00 JST) に自動実行されます。時刻を変えたい場合は `cron` の値を編集してください。
- 動作確認は Actions タブから `Daily Shorts Auto-Post` を **workflow_dispatch(手動実行)** で試せます。

## 投稿タイトル・キャプション

YouTube のタイトルは全動画共通で `VIDEO_TITLE`(デフォルト `POTE daily shorts`)を使います。説明欄/TikTokのキャプションは Drive 上のファイル名(拡張子を除く)がベースになり、`HASHTAGS` を末尾に追記します。個別の動画ごとに凝ったキャプションを付けたい場合は、ファイル名に工夫するか `src/main.py` の `build_caption()` を拡張してください。

## 状態ファイル (`state/queue_state.json`)

```json
{
  "cycle": 2,
  "order": ["fileIdA", "fileIdC", "fileIdB"],
  "cursor": 1,
  "pending": null,
  "history": [
    {
      "posted_at": "2026-08-14T21:00:03+00:00",
      "cycle": 2,
      "file_id": "fileIdA",
      "file_name": "example.mp4",
      "youtube_video_id": "xxxxxxxxxxx",
      "tiktok_publish_id": "v_pub_url~xxxx"
    }
  ]
}
```

このファイルは Actions の実行のたびに自動コミットされるため、手動で編集しないでください(やり直したい場合は `cursor` を `0` に、`order` を `[]` にリセットすると次回実行時に新しいサイクルとして再シャッフルされます)。

## ローカルでの動作確認

```bash
pip install -r requirements.txt
cp .env.example .env   # 値を埋める
export $(grep -v '^#' .env | xargs)
python -m src.main
```

## 制限事項・注意点

- YouTube Shorts として認識されるのは、動画が縦長(または正方形)かつ長さがおおむね3分以内の場合です。アップロードAPI自体に「Shorts」を指定するフラグはなく、YouTube側が動画の形状・長さから自動判定します。
- TikTok・YouTube ともに1日あたりのAPI投稿数・容量に制限があります。大量の動画を一度に投稿する運用には向きません(このBotは1日1本を想定)。
- TikTok のリフレッシュトークンは失効・ローテーションする場合があります。ローテーションが発生すると Actions のログに warning が出力されるので、その値で `TIKTOK_REFRESH_TOKEN` シークレットを更新してください。
- `state/queue_state.json` をコミットバックする都合上、このリポジトリを **Private** にしておくことを推奨します(動画ファイル名や投稿履歴が含まれるため)。
