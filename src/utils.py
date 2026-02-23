
import logging
from datetime import datetime

import pandas as pd
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_datetime(date_string):
    """
    Парсит строку даты и времени в объект datetime.
    """
    try:
        parsed_date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        logger.info(f"Успешно распарсена дата: {date_string}")
        return parsed_date
    except ValueError as e:
        logger.error(f"Ошибка парсинга даты {date_string}: {e}")
        raise ValueError("Неверный формат даты. Ожидаемый формат: YYYY-MM-DD HH:MM:SS")


def fetch_external_data(date_str):
    """
    Получает внешние данные для указанной даты.

    Args:
        date_str (str): Дата в формате 'YYYY-MM-DD'

    Returns:
        dict or None: Данные в виде словаря или None при ошибке
    """
    url = "https://api.example.com/data"
    params = {"date": date_str}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Вызывает HTTPError для 4xx/5xx кодов
        return response.json()
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError, ValueError) as e:
        logging.warning(f"Ошибка при получении данных для даты {date_str}: {e}")
        return None

def process_data_with_pandas(raw_data):
    """
    Обрабатывает данные с использованием pandas.
    """
    if not raw_data:
        return []

    # Преобразуем в DataFrame
    df = pd.DataFrame(raw_data)

    # Пример обработки: преобразуем строки с датами в datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Простая агрегация — считаем количество записей по группам
    if 'category' in df.columns:
        summary = df.groupby('category').size().reset_index(name='count')
        result = summary.to_dict('records')
    else:
        result = df.to_dict('records')

    logger.info("Данные успешно обработаны с помощью pandas")
    return result


def format_response(data, input_date):
    """
    Формирует финальный JSON-ответ.
    """
    response = {
        "status": "success",
        "input_date": input_date,
        "processed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "data": data,
        "total_records": len(data) if isinstance(data, list) else 0
    }
    return response
