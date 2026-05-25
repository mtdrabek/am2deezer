# am2deezer

A Telegram bot that converts Apple Music track links to Deezer links.

Send it a link — get a link back.

```
https://music.apple.com/in/album/atsiprashow/1462803914?i=1462803916
        ↓
https://www.deezer.com/track/676524552
```

## How it works

1. Extracts the track ID from the Apple Music URL
2. Fetches metadata (artist, title) from the iTunes Lookup API — no API key needed
3. Searches the Deezer API — also no API key needed
4. Returns the Deezer link

No third-party music APIs, no auth tokens, no scraping. Just two public APIs.

## Deploy on Railway (free)

### 1. Get a Telegram bot token

Talk to [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token.

### 2. Fork or clone this repo

```bash
git clone https://github.com/mtdrabek/am2deezer.git
cd am2deezer
```

### 3. Deploy

- Go to [railway.app](https://railway.app) and sign in with GitHub
- New Project → Deploy from GitHub repo → select this repo
- Open the service → **Variables** tab → add:

| Name | Value |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | your token from BotFather |

- Railway will deploy automatically. That's it.

The free tier gives 500 hours/month — enough for a personal bot running on polling.

## Run locally

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=your_token_here
python bot.py
```

## Limitations

- Tracks only (no albums, no artists)
- If a track exists on Apple Music but not on Deezer, the bot will say so
- Deezer search is fuzzy — for obscure releases it might return a wrong result
