import os, html, random
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

CAPTION_LIMIT = 1024
EMOJIS = ["📰", "⚡", "❗", "⭐", "💰"]

def _escape(t: str) -> str:
    return html.escape(t or "", quote=False)

def _trim_caption(html_text: str) -> str:
    # простое обрезание по лимиту, не ломая теги (на практике работает ок для наших коротких текстов)
    if len(html_text) <= CAPTION_LIMIT:
        return html_text
    # укорачиваем содержимое между тегами, если нужно
    return html_text[:CAPTION_LIMIT - 1] + "…"

async def post_to_telegram(
    gpt_title: str,
    link: str,
    summary_ru: str,
    image_url: str | None = None,
    *,
    raw_html: bool = False,   # 🔹 НОВОЕ: разрешить готовый HTML без экранирования
    with_link: bool = True    # можно выключить ссылку для “итогов дня”
):
    emoji = random.choice(EMOJIS)
    # если raw_html=True — не экранируем
    title_html   = gpt_title   if raw_html else _escape(gpt_title)
    summary_html = summary_ru  if raw_html else _escape(summary_ru)
    link_html    = f"\n\n<a href='{_escape(link)}'>Источник</a>" if (with_link and link) else ""

    if image_url:
        caption = f"{emoji} <b>{title_html}</b>\n\n{summary_html}{link_html}"
        caption = _trim_caption(caption)
        await bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=caption, parse_mode="HTML")
    else:
        text = f"{emoji} <b>{title_html}</b>\n\n{summary_html}{link_html}"
        await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML", disable_web_page_preview=False)

    print(f"✅ Posted: {emoji} {gpt_title}")
