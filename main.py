import asyncio
from datetime import datetime, time, date
from news_parser import fetch_latest_articles
from gpt_client import summarize_article
from telegram_bot import post_to_telegram

# --- настройки ---
ACTIVE_START = time(8, 0)
ACTIVE_END = time(23, 0)
CHECK_INTERVAL_MINUTES = 15

# глобальный список новостей за день
daily_titles = []
last_summary_date = date.today()


def is_active_hours() -> bool:
    """Проверяет, сейчас ли время публикации (между 8:00 и 23:00)."""
    now = datetime.now().time()
    return ACTIVE_START <= now <= ACTIVE_END


async def post_daily_summary():
    """Публикует в Telegram сводку за день."""
    global daily_titles

    if not daily_titles:
        print("📭 За день не было новостей — итог не публикуется.")
        return

    # собираем сообщение
    today_str = datetime.now().strftime("%d.%m.%Y")
    header = f"🗞 <b>Итоги дня ({today_str})</b>\n\n"
    body = "\n".join([f"• {t}" for t in daily_titles])
    text = header + body

    try:
        await post_to_telegram("Итоги дня", "", text)
        print("✅ Опубликованы итоги дня.")
    except Exception as e:
        print(f"[Summary ERROR] {e}")

    # очищаем список новостей на следующий день
    daily_titles = []


async def main_loop():
    global last_summary_date, daily_titles

    while True:
        now = datetime.now()
        current_time = now.time()

        # ежедневная проверка: новый день → обнуляем список
        if date.today() != last_summary_date:
            print("📅 Новый день — очищаем список новостей.")
            daily_titles = []
            last_summary_date = date.today()

        # если вечер и пора подвести итоги
        if current_time.hour == 23 and current_time.minute < CHECK_INTERVAL_MINUTES:
            print("🕚 Время итогов дня...")
            await post_daily_summary()
            await asyncio.sleep(60)  # подождать минуту, чтобы не дублировать
            continue

        # если не активные часы — спим
        if not is_active_hours():
            print("🌙 Ночь — бот спит до утра...")
            await asyncio.sleep(CHECK_INTERVAL_MINUTES * 60)
            continue

        # обычный парсинг
        print("🔄 Проверяем новые новости...")
        articles = await fetch_latest_articles()

        if not articles:
            print("Нет новых статей.")
        else:
            for article in articles:
                print(f"📰 Обрабатываем: {article['title']}")
                gpt = await summarize_article(article)
                if not gpt:
                    continue

                # публикуем в Telegram
                await post_to_telegram(
                    gpt_title=gpt["title"],
                    link=article["link"],
                    summary_ru=gpt["summary"],
                    image_url=article.get("image_url"),
                )

                # добавляем заголовок в список итогов
                daily_titles.append(gpt["title"])

        print(f"💤 Спим {CHECK_INTERVAL_MINUTES} минут...\n")
        await asyncio.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    asyncio.run(main_loop())
