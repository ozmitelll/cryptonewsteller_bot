import asyncio
import random
from datetime import datetime, time, date
from news_parser import fetch_latest_articles
from gpt_client import summarize_article
from telegram_bot import post_to_telegram

# --- настройки ---
ACTIVE_START = time(8, 0)
ACTIVE_END   = time(23, 00)  # время, КОГДА уже можно подводить итоги
CHECK_INTERVAL_MINUTES = 5
POST_DELAY_RANGE = (60, 180)

daily_titles = []
summary_date = date.today()
daily_summary_posted = False  # <- флаг «итоги уже опубликованы сегодня?»

def is_active_hours() -> bool:
    now = datetime.now().time()
    return ACTIVE_START <= now <= ACTIVE_END

async def post_daily_summary():
    global daily_titles, daily_summary_posted
    if not daily_titles:
        print("📭 За день не было новостей — итог не публикуется.")
        daily_summary_posted = True
        return

    emojis = ["⚡", "💰", "🌐", "⭐", "🚀", "📈", "📉", "💎", "🪙", "🔥"]
    formatted_items = [f"{random.choice(emojis)} <b>{t}</b>" for t in daily_titles]
    body = "\n\n".join(formatted_items)

    await post_to_telegram("Итоги дня", "", body, image_url=None, raw_html=True, with_link=False)
    print("✅ Опубликованы итоги дня.")
    daily_titles = []
    daily_summary_posted = True

async def main_loop():
    global summary_date, daily_titles, daily_summary_posted

    while True:
        now_dt = datetime.now()

        # Новый день — сбрасываем накопление и флаг итогов
        if date.today() != summary_date:
            print("📅 Новый день — очищаем список новостей и флаг итогов.")
            daily_titles = []
            summary_date = date.today()
            daily_summary_posted = False

        # Если наступило/прошло время итогов и итоги ещё не публиковались — публикуем
        if (now_dt.time() >= ACTIVE_END) and (not daily_summary_posted):
            print("🕚 Время итогов дня...")
            await post_daily_summary()
            # небольшая пауза, чтобы не задублировать
            await asyncio.sleep(60)
            continue

        # Ночь — не постим, просто ждём
        if not is_active_hours():
            print("🌙 Ночь — бот спит до окна активности...")
            await asyncio.sleep(CHECK_INTERVAL_MINUTES * 60)
            continue

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

                await post_to_telegram(
                    gpt_title=gpt["title"],
                    link=article["link"],
                    summary_ru=gpt["summary"],
                    image_url=article.get("image_url"),
                )
                daily_titles.append(gpt["title"])

                delay = random.randint(*POST_DELAY_RANGE)
                print(f"⏳ Ждём {delay} сек перед следующим постом...")
                await asyncio.sleep(delay)

        print(f"💤 Спим {CHECK_INTERVAL_MINUTES} минут...\n")
        await asyncio.sleep(CHECK_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    asyncio.run(main_loop())
