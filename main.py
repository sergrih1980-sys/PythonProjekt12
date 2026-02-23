import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- ФУНКЦИИ ИЗ utils.py ---

def parse_datetime(date_string: str) -> datetime:
    """Парсит строку даты и времени в объект datetime."""
    try:
        parsed_date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        logger.info(f"Успешно распарсена дата: {date_string}")
        return parsed_date
    except ValueError as e:
        logger.error(f"Ошибка парсинга даты {date_string}: {e}")
        raise ValueError("Неверный формат даты. Ожидаемый формат: YYYY-MM-DD HH:MM:SS")

def fetch_external_data(date_str: str) -> Optional[Dict[Any, Any]]:
    """Получает внешние данные для указанной даты."""
    url = "https://api.example.com/data"
    params = {"date": date_str}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError, ValueError) as e:
        logging.warning(f"Ошибка при получении данных для даты {date_str}: {e}")
        return None

def process_data_with_pandas(raw_data: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
    """Обрабатывает данные с использованием pandas."""
    if not raw_data:
        return []

    df = pd.DataFrame(raw_data)

    # Преобразуем строки с датами в datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Агрегация — считаем количество записей по группам
    if 'category' in df.columns:
        summary = df.groupby('category').size().reset_index(name='count')
        result = summary.to_dict('records')
    else:
        result = df.to_dict('records')

    logger.info("Данные успешно обработаны с помощью pandas")
    return result

def format_response(data: Any, input_date: str) -> Dict[str, Any]:
    """Формирует финальный JSON‑ответ."""
    response = {
        "status": "success",
        "input_date": input_date,  # Исправлено: было inputdate
        "processed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "data": data,
        "total_records": len(data) if isinstance(data, list) else 0
    }
    return response

# --- ГЛАВНАЯ СТРАНИЦА ---

def home_page(date_string: str) -> str:
    """Главная страница — получает и обрабатывает данные."""
    try:
        raw_data = fetch_external_data(date_string)

        if raw_data is None:
            logger.warning("Не удалось получить данные из API, используем заглушку")
            raw_data = [
                {"id": 1, "value": "test1", "category": "A"},
                {"id": 2, "value": "test2", "category": "B"}
            ]

        processed_data = process_data_with_pandas(raw_data)
        response_data = format_response(processed_data, date_string)
        logger.info(f"Страница 'Главная' успешно обработана для даты: {date_string}")

        return json.dumps(response_data, ensure_ascii=False, indent=2)
    except Exception as e:
        error_response = {
            "status": "error",
            "message": str(e),
            "input_date": date_string,
            "processed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        logger.error(f"Ошибка в функции home_page: {e}")
        return json.dumps(error_response, ensure_ascii=False, indent=2), 500

# --- ПРОСТОЙ ПОИСК ---

def simple_search(search_query: str, transactions: List[Dict[str, Any]]) -> str:
    """Функция сервиса «Простой поиск»."""
    try:
        logger.info(f"Запуск поиска с запросом: '{search_query}'")
        normalized_query = search_query.strip().lower()

        if not normalized_query:
            logger.warning("Получен пустой поисковый запрос")
            return _format_response([], search_query, 0)

        found_transactions = []
        for transaction in transactions:
            match_found = False
            for key, value in transaction.items():
                if isinstance(value, str):
                    if normalized_query in value.lower():
                        match_found = True
                        break
            if match_found:
                found_transactions.append(transaction)

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
    """Вспомогательная функция для формирования JSON‑ответа."""
    response = {
        "status": "success",
        "search_query": query,
        "found_count": count,
        "results": results
    }
    return json.dumps(response, ensure_ascii=False, indent=2)

# --- ОТЧЁТ ПО РАСХОДАМ ---

def expenses_by_category(
    df: pd.DataFrame,
    category: str,
    reference_date: str
) -> str:
    """Формирует отчёт по расходам для указанной категории за последние 90 дней."""
    try:
        ref_date = datetime.strptime(reference_date, '%Y-%m-%d')
        period_start = ref_date - timedelta(days=90)

        df_copy = df.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce')

        filtered_df = df_copy[
            (df_copy['date'].notna()) &
            (df_copy['date'] >= period_start) &
            (df_copy['date'] <= ref_date) &
            (df_copy['category'] == category)
        ]

        if filtered_df.empty:
            return json.dumps({
                "status": "success",
                "category": category,
                "reference_date": reference_date,
                "period_start": period_start.strftime('%Y-%m-%d'),
                "period_end": reference_date,
                "total_amount": 0.00,
                "transaction_count": 0,
                "monthly_breakdown": []
            })

        total_amount = float(filtered_df['amount'].sum())
        transaction_count = len(filtered_df)

        monthly_breakdown = []
        for month, group in filtered_df.groupby(filtered_df['date'].dt.to_period('M')):
            monthly_breakdown.append({
                "month": month.strftime('%Y-%m'),
                "amount": float(group['amount'].sum())
            })

        return json.dumps({
            "status": "success",
            "category": category,
            "reference_date": reference_date,
            "period_start": period_start.strftime('%Y-%m-%d'),
            "period_end": reference_date,
            "total_amount": round(total_amount, 2),
            "transaction_count": transaction_count,
            "monthly_breakdown": monthly_breakdown
        })

    except Exception as e:
        logger.error(f"Ошибка в функции expenses_by_category: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


# --- ТРАТЫ ПО КАТЕГОРИИ ---

def spending_by_category(
        transactions: pd.DataFrame,
        category: str,
        date: Optional[str] = None
) -> pd.DataFrame:
    """Возвращает траты по заданной категории за последние три месяца."""
    try:
        # Если дата не передана, берём текущую
        if date is None:
            ref_date = datetime.now()
        else:
            try:
                ref_date = datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Неверный формат даты. Ожидаемый формат: YYYY-MM-DD")

        # Расчёт периода: 90 дней назад от reference_date
        period_start = ref_date - timedelta(days=90)

        # Конвертация дат в DataFrame с обработкой ошибок
        transactions['date'] = pd.to_datetime(transactions['date'], errors='coerce')

        # Фильтрация: только корректные даты в периоде и нужной категории
        filtered_df = transactions[
            (transactions['date'].notna()) &
            (transactions['date'] >= period_start) &
            (transactions['date'] <= ref_date) &
            (transactions['category'] == category)
            ]

        logger.info(
            f"Отфильтровано {len(filtered_df)} транзакций по категории '{category}' "
            f"за период {period_start.date()} – {ref_date.date()}"
        )
        return filtered_df

    except Exception as e:
        logger.error(f"Ошибка в функции spending_by_category: {e}")
        raise


# --- ПРИВЕТСТВИЕ И ГЕНЕРАЦИЯ ОТВЕТА ---

def get_greeting(hour: int) -> str:
    """Определяет приветствие в зависимости от часа."""
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 17:
        return "Добрый день"
    elif 17 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def generate_response(input_date_string: str) -> str:
    """
    Главная функция, принимающая строку с датой и временем и возвращающая JSON-ответ.
    """
    try:
        # Парсим входную дату
        input_datetime = datetime.strptime(input_date_string, '%Y-%m-%d %H:%M:%S')
        hour = input_datetime.hour

        # Приветствие
        greeting = get_greeting(hour)

        # Пример данных для демонстрации
        cards_data = [
            {"last_digits": "5814", "total_spent": 1262.00, "cashback": 12.62},
            {"last_digits": "7512", "total_spent": 7.94, "cashback": 0.08}
        ]

        top_transactions = [
            {
                "date": "21.12.2021",
                "amount": 1198.23,
                "category": "Переводы",
                "description": "Перевод Кредитная карта. ТП 10.2 RUR"
            },
            {
                "date": "20.12.2021",
                "amount": 829.00,
                "category": "Супермаркеты",
                "description": "Лента"
            },
            {
                "date": "20.12.2021",
                "amount": 421.00,
                "category": "Различные товары",
                "description": "Ozon.ru"
            },
            {
                "date": "16.12.2021",
                "amount": -14216.42,
                "category": "ЖКХ",
                "description": "ЖКУ Квартира"
            },
            {
                "date": "16.12.2021",
                "amount": 453.00,
                "category": "Бонусы",
                "description": "Кешбэк за обычные покупки"
            }
        ]

        currency_rates = [
            {"currency": "USD", "rate": 73.21},
            {"currency": "EUR", "rate": 87.08}
        ]

        stock_prices = [
            {"stock": "AAPL", "price": 150.12},
            {"stock": "AMZN", "price": 3173.18},
            {"stock": "GOOGL", "price": 2742.39},
            {"stock": "MSFT", "price": 296.71},
            {"stock": "TSLA", "price": 1007.08}
        ]

        # Формируем итоговый JSON-ответ
        response = {
            "greeting": greeting,
            "cards": cards_data,
            "top_transactions": top_transactions,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices
        }

        logger.info(f"JSON-ответ успешно сформирован для даты: {input_date_string}")
        return json.dumps(response, ensure_ascii=False, indent=2)
    except ValueError as e:
        error_response = {
            "status": "error",
            "message": (
                f"Неверный формат даты: {str(e)}. "
                "Ожидаемый формат: YYYY-MM-DD HH:MM:SS"
            ),
            "input_date": input_date_string,
            "processed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        logger.error(f"Ошибка парсинга даты: {e}")
        return json.dumps(error_response, ensure_ascii=False, indent=2)
    except Exception as e:
        error_response = {
            "status": "error",
            "message": str(e),
            "input_date": input_date_string,
            "processed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        logger.error(f"Неожиданная ошибка в generate_response: {e}")
        return json.dumps(error_response, ensure_ascii=False, indent=2)


# --- ТОЧЕЧКА ВХОДА ---

if __name__ == '__main__':
    # Пример использования функций
    print("=== Главная страница ===")
    print(home_page("2024-01-15"))

    print("\n=== Простой поиск ===")
    sample_transactions = [
        {"id": 1, "name": "Покупка в магазине", "category": "Продукты"},
        {"id": 2, "name": "Оплата интернета", "category": "Услуги"}
    ]
    print(simple_search("магазин", sample_transactions))

    print("\n=== Отчёт по расходам ===")
    sample_df = pd.DataFrame([
        {"date": "2024-01-01", "amount": 100.0, "category": "Продукты"},
        {"date": "2024-01-15", "amount": 200.0, "category": "Продукты"}
    ])
    print(expenses_by_category(sample_df, "Продукты", "2024-02-01"))

    print("\n=== Генерация ответа ===")
    print(generate_response("2024-01-15 14:30:00"))