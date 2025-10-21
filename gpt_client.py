# gpt_client.py
import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM = "Ты — редактор новостей. Пиши кратко, нейтрально и по-деловому на русском языке."

USER_TMPL = """
Сформируй ПЕРЕФОРМУЛИРОВАННЫЙ И ПЕРЕВЕДЁННЫЙ заголовок на русском и краткое резюме (3–4 предложения).
И не указывай в ответах к примеру (В этой статье, и тд.)
Верни строго JSON с полями:
- title: строка — новый заголовок на русском (коротко, без кликабейта)
- summary: строка — краткое содержание на русском

Данные статьи:
Заголовок: {title}
Текст новости:
{content}
"""

async def summarize_article(article: dict) -> dict | None:
    """
    Возвращает dict: {"title": "...", "summary": "..."}  — оба на русском.
    В случае ошибки вернёт None.
    """
    title = (article.get("title") or "").strip()
    content = (article.get("content") or "").strip()

    # при очень длинных текстах можно слегка урезать для экономии токенов
    if len(content) > 5000:
        content = content[:5000] + "…"

    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": USER_TMPL.format(title=title, content=content)},
            ],
            temperature=0.4,
            response_format={"type": "json_object"},  # просим строго JSON
        )
        raw = resp.choices[0].message.content
        data = json.loads(raw)
        # минимальная валидация
        return {
            "title": data.get("title", "").strip() or title,
            "summary": data.get("summary", "").strip(),
        }
    except Exception as e:
        print(f"[GPT ERROR] {e}")
        return None
