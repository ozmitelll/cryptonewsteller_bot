import asyncio
from news_parser import fetch_latest_articles
from gpt_client import summarize_article
from telegram_bot import post_to_telegram

async def main_loop():
    while True:
        print("🔄 Проверяем новые новости...")
        articles = await fetch_latest_articles()

        if not articles:
            print("Нет новых статей.")
        else:
            for article in articles:
                print(f"📰 Обрабатываем: {article['title']}")
                gpt = await summarize_article(article)
                if not gpt:
                    print("⏭ Пропущено (GPT недоступен).")
                    continue

                await post_to_telegram(
                    gpt_title=gpt["title"],
                    link=article["link"],
                    summary_ru=gpt["summary"] or "(нет краткого содержания)",
                    image_url=article.get("image_url"),
                )

        print("💤 Спим 5 минут...\n")
        await asyncio.sleep(5 * 60)

if __name__ == "__main__":
    asyncio.run(main_loop())
