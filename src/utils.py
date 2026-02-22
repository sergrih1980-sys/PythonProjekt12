
import logging
import pandas as pd
from datetime import datetime
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
        raise ValueError(f"Неверный формат даты. Ожидаемый формат: YYYY-MM-DD HH:MM:SS")


def fetch_external_data(api_url, params=None):
    """
    Получает данные из внешнего API.
    """
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Успешно получены данные из API")
        return data
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
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
