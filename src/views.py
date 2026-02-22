import json
import logging
from datetime import datetime

from src.utils import fetch_external_data, format_response, process_data_with_pandas

logger = logging.getLogger(__name__)


def home_page(date_string):
    try:
        api_url = "https://api.example.com/data"
        api_params = {"date": date_string}
        raw_data = fetch_external_data(api_url, api_params)

        if raw_data is None:
            logger.warning("Не удалось получить данные из API, используем заглушку")
            raw_data = [
                {"id": 1, "value": "test1", "category": "A"},
                {"id": 2, "value": "test2", "category": "B"}
            ]

        processed_data = process_data_with_pandas(raw_data)
        response_data = format_response(processed_data, date_string)

        logger.info(f"Страница 'Главная' успешно обработана для даты: {date_string}")

        # json.dumps возвращает строку JSON
        return json.dumps(response_data, ensure_ascii=False, indent=2)

    except Exception as e:
        error_response = {
            "status": "error",
            "message": str(e),
            "input_date": date_string,
            "processed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        logger.error(f"Ошибка в функции home_page: {e}")
        # Для ошибок можно вернуть кортеж (JSON, HTTP-статус)
        return json.dumps(error_response, ensure_ascii=False, indent=2), 500
