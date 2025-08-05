import requests
import logging
import schedule
import time
from datetime import datetime, timedelta
from config import TELEGRAM_TOKEN, TELEGRAM_CHANNEL_ID, HEADERS

# Настройка логирования
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def get_funding_rates():
    """Получает funding rates с биржи BingX"""
    url = "https://open-api.bingx.com/openApi/swap/v2/quote/premiumIndex"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        logging.error(f"Ошибка при получении данных: {e}")
        return []

def format_funding_message(tokens, timestamp_utc):
    """Формирует сообщение для Telegram"""
    if not tokens:
        return "❌ Не удалось получить ставки финансирования."

    formatted_tokens = []
    for item in tokens:
        symbol = item["symbol"]
        rate = float(item["fundingRate"]) * 100
        formatted_tokens.append(f"{symbol}: {rate:.4f}%")

    message = (
        f"💰 ТОП 5 минимальных funding rate на {timestamp_utc.strftime('%Y-%m-%d %H:%M UTC')}:\n\n"
        + "\n".join(formatted_tokens)
    )
    return message

def send_telegram_message(message: str):
    """Отправляет сообщение в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logging.info("Сообщение успешно отправлено в Telegram.")
    except Exception as e:
        logging.error(f"Ошибка при отправке в Telegram: {e}")

def job():
    """Основная задача"""
    logging.info("⏱ Выполнение задания...")
    all_tokens = get_funding_rates()
    if not all_tokens:
        logging.warning("⚠️ Получено 0 токенов.")
        return

    # Сортировка по fundingRate по возрастанию
    sorted_tokens = sorted(all_tokens, key=lambda x: float(x["fundingRate"]))
    top_5 = sorted_tokens[:5]

    utc_now = datetime.utcnow()
    message = format_funding_message(top_5, utc_now)
    send_telegram_message(message)

# Регистрируем задание за 10 минут до каждого часа (в 50 минут каждого часа)
schedule.every().hour.at(":50").do(job)

if __name__ == "__main__":
    logging.info("🚀 Бот стартует")
    print("🚀 Бот стартует")

    while True:
        schedule.run_pending()
        time.sleep(1)
