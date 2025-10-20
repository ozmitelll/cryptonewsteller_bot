import os, html, random
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

CAPTION_LIMIT = 1024  # лимит подписи sendPhoto

# набор эмодзи для заголовка
EMOJIS = ["📰", "⚡", "❗", "⭐", "💰"]

def random_emoji() -> str:
    """Возвращает случайную иконку."""
    return random.choice(EMOJIS)

def _escape(t: str) -> str:
    return html.escape(t or "", quote=False)

def _caption(title: str, summary: str, link: str) -> str:
    emoji = random_emoji()
    text = f"{emoji} <b>{_escape(title)}</b>\n\n{_escape(summary)}\n\n"
    if len(text) > CAPTION_LIMIT:
        over = len(text) - CAPTION_LIMIT
        cut = max(0, len(summary) - (over + 3))
        summary = (summary[:cut].rstrip() + "…") if cut > 0 else ""
        text = f"{emoji} <b>{_escape(title)}</b>\n\n{_escape(summary)}\n\n"
    return text

async def post_to_telegram(gpt_title: str, link: str, summary_ru: str, image_url: str | None = None):
    emoji = random_emoji()  # чтобы одинаково для photo и text
    try:
        if image_url:
            caption = f"{emoji} <b>{_escape(gpt_title)}</b>\n\n{_escape(summary_ru)}\n\n"
            if len(caption) > CAPTION_LIMIT:
                over = len(caption) - CAPTION_LIMIT
                cut = max(0, len(summary_ru) - (over + 3))
                summary_ru = (summary_ru[:cut].rstrip() + "…") if cut > 0 else ""
                caption = f"{emoji} <b>{_escape(gpt_title)}</b>\n\n{_escape(summary_ru)}\n\n"
            await bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=caption, parse_mode="HTML")
        else:
            text = f"{emoji} <b>{_escape(gpt_title)}</b>\n\n{_escape(summary_ru)}\n\n"
            await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML", disable_web_page_preview=False)
        print(f"✅ Posted: {emoji} {gpt_title}")
    except Exception as e:
        print(f"[Telegram ERROR] {e}")
