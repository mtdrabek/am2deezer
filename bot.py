import os
import re
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APPLE_MUSIC_RE = re.compile(
    r"https?://music\.apple\.com/[a-z]{2}/album/[^/]+/(\d+)\?.*i=(\d+)"
    r"|https?://music\.apple\.com/[a-z]{2}/album/[^/]+/(\d+)"
)


def extract_itunes_id(url: str) -> tuple[str | None, str]:
    """
    Returns (itunes_track_id_or_album_id, kind)
    kind: 'track' | 'album'
    """
    # Track link has ?i=TRACKID
    track_match = re.search(r"[?&]i=(\d+)", url)
    if track_match:
        return track_match.group(1), "track"

    # Fallback: album id at end of path
    album_match = re.search(r"/album/[^/]+/(\d+)", url)
    if album_match:
        return album_match.group(1), "album"

    return None, "unknown"


def itunes_lookup(itunes_id: str, kind: str) -> dict | None:
    entity = "song" if kind == "track" else "album"
    url = f"https://itunes.apple.com/lookup?id={itunes_id}&entity={entity}&limit=1"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        # For track links, first result is album, second is track
        for item in results:
            if kind == "track" and item.get("wrapperType") == "track":
                return item
            if kind == "album" and item.get("wrapperType") == "collection":
                return item
        # fallback: return first result
        return results[0] if results else None
    except Exception as e:
        logger.error(f"iTunes lookup failed: {e}")
        return None


def deezer_search_track(artist: str, title: str) -> str | None:
    query = f'artist:"{artist}" track:"{title}"'
    url = "https://api.deezer.com/search"
    try:
        r = requests.get(url, params={"q": query, "limit": 1}, timeout=10)
        r.raise_for_status()
        data = r.json()
        items = data.get("data", [])
        if items:
            return f"https://www.deezer.com/track/{items[0]['id']}"
        # fallback: looser search
        r2 = requests.get(url, params={"q": f"{artist} {title}", "limit": 1}, timeout=10)
        r2.raise_for_status()
        data2 = r2.json()
        items2 = data2.get("data", [])
        if items2:
            return f"https://www.deezer.com/track/{items2[0]['id']}"
    except Exception as e:
        logger.error(f"Deezer search failed: {e}")
    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if "music.apple.com" not in text:
        await update.message.reply_text("Скинь ссылку на трек из Apple Music.")
        return

    itunes_id, kind = extract_itunes_id(text)
    if not itunes_id:
        await update.message.reply_text("Не смог распарсить ссылку. Убедись что это ссылка на конкретный трек.")
        return

    if kind != "track":
        await update.message.reply_text("Пока работаю только с треками. Скинь ссылку на трек (не на альбом).")
        return

    await update.message.reply_text("⏳ Ищу...")

    meta = itunes_lookup(itunes_id, kind)
    if not meta:
        await update.message.reply_text("Не нашёл трек в iTunes. Попробуй ещё раз.")
        return

    artist = meta.get("artistName", "")
    title = meta.get("trackName", "")

    if not artist or not title:
        await update.message.reply_text("Не удалось получить метаданные трека.")
        return

    deezer_url = deezer_search_track(artist, title)
    if deezer_url:
        await update.message.reply_text(
            f"🎵 *{artist} — {title}*\n\n{deezer_url}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"Нашёл трек: *{artist} — {title}*, но в Deezer не нашёл. Возможно, его там нет.",
            parse_mode="Markdown"
        )


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
