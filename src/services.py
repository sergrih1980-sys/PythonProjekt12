import json
import logging
from typing import Any, Dict, List

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def simple_search(search_query: str, transactions: List[Dict[str, Any]]) -> str:
    """
    Функция сервиса «Простой поиск».

    Принимает:
    - search_query (str): строка — запрос для поиска;
    - transactions (List[Dict]): список словарей с транзакциями.

    Возвращает:
    - JSON‑строку с результатами поиска согласно ТЗ.
    """
    try:
        logger.info(f"Запуск поиска с запросом: '{search_query}'")

        # Нормализуем поисковый запрос — приводим к нижнему регистру и убираем лишние пробелы
        normalized_query = search_query.strip().lower()

        if not normalized_query:
            logger.warning("Получен пустой поисковый запрос")
            return _format_response([], search_query, 0)

        # Список для хранения найденных транзакций
        found_transactions = []

        # Перебираем все транзакции и ищем совпадения
        for transaction in transactions:
            # Проверяем совпадение в каждом поле транзакции (только строковые поля)
            match_found = False
            for key, value in transaction.items():
                if isinstance(value, str):
                    if normalized_query in value.lower():
                        match_found = True
                        break

            if match_found:
                found_transactions.append(transaction)

        # Формируем JSON‑ответ
        result = _format_response(found_transactions, search_query, len(found_transactions))
        logger.info(f"Поиск завершён. Найдено {len(found_transactions)} транзакций")
        return result

    except Exception as e:
        error_message = f"Ошибка в функции simple_search: {str(e)}"
        logger.error(error_message)
        error_response = {
            "status": "error",
            "message": error_message,
            "search_query": search_query,
            "found_count": 0,
            "results": []
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)


def _format_response(results: List[Dict[str, Any]], query: str, count: int) -> str:
    """
    Вспомогательная функция для формирования JSON‑ответа.
    """
    response = {
        "status": "success",
        "search_query": query,
        "found_count": count,
        "results": results
    }
    return json.dumps(response, ensure_ascii=False, indent=2)
