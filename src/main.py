import json
import logging
import pandas as pd
from datetime import datetime, timedelta
import requests
from typing import List, Dict, Any

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_datetime(date_string: str) -> datetime:
    """Парсит строку даты и времени в объект datetime."""
    try:
        parsed_date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        logger.info(f"Успешно распарсена дата: {date_string}")
        return parsed_date
    except ValueError as e:
        logger.error(f"Ошибка парсинга даты {date_string}: {e}")
        raise ValueError("Неверный формат даты. Ожидаемый формат: YYYY-MM-DD HH:MM:SS")


def fetch_external_data(api_url: str, params: Dict = None) -> Any:
    """Получает данные из внешнего API."""
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Успешно получены данные из API")
        return data
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return None


def process_data_with_pandas(raw_data: List[Dict]) -> List[Dict]:
    """Обрабатывает данные с использованием pandas."""
    if not raw_data:
        return []

    df = pd.DataFrame(raw_data)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    if 'category' in df.columns:
        summary = df.groupby('category').size().reset_index(name='count')
        result = summary.to_dict('records')
    else:
        result = df.to_dict('records')

    logger.info("Данные успешно обработаны с помощью pandas")
    return result


def format_response(data: List[Dict], input_date: str) -> str:
    """Формирует финальный JSON‑ответ для главной страницы."""
    response = {
        "status": "success",
        "input_date": input_date,
        "processed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "data": data,
        "total_records": len(data) if isinstance(data, list) else 0
    }
    return json.dumps(response, ensure_ascii=False, indent=2)


def _format_search_response(results: List[Dict[str, Any]], query: str, count: int) -> str:
    """Вспомогательная функция для формирования JSON‑ответа поиска."""
    response = {
        "status": "success",
        "search_query": query,
        "found_count": count,
        "results": results
    }
    return json.dumps(response, ensure_ascii=False, indent=2)


def _format_expenses_response(
    monthly_data: list,
    category: str,
    reference_date: str,
    total_amount: float,
    transaction_count: int
) -> str:
    """Вспомогательная функция для формирования JSON‑ответа отчёта."""
    start_date = (datetime.strptime(reference_date, '%Y-%m-%d') - timedelta(days=90)).strftime('%Y-%m-%d')
    response = {
        "status": "success",
        "category": category,
        "reference_date": reference_date,
        "period_start": start_date,
        "period_end": reference_date,
        "total_amount": round(total_amount, 2),
        "transaction_count": transaction_count,
        "monthly_breakdown": monthly_data
    }
    return json.dumps(response, ensure_ascii=False, indent=2)


def home_page(date_string: str) -> str:
    """Обработка главной страницы."""
    try:
        api_url = "https://api.example.com/data"  # Обратите внимание: вероятно, должно быть "https://"
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
        return response_data

    except Exception as e:
        error_response = {
            "status": "error",
            "message": str(e),
            "input_date": date_string,
            "processed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        logger.error(f"Ошибка в функции home_page: {e}")
        return json.dumps(error_response, ensure_ascii=False, indent=2), 500


def simple_search(search_query: str, transactions: List[Dict[str, Any]]) -> str:
    """Функция сервиса «Простой поиск»."""
    try:
        logger.info(f"Запуск поиска с запросом: '{search_query}'")
        normalized_query = search_query.strip().lower()

        if not normalized_query:
            logger.warning("Получен пустой поисковый запрос")
            return _format_search_response([], search_query, 0)

        found_transactions = []
        for transaction in transactions:
            match_found = False
            for key, value in transaction.items():
                if isinstance(value, str) and normalized_query in value.lower():
                    match_found = True
                    break
            if match_found:
                found_transactions.append(transaction)

        result = _format_search_response(found_transactions, search_query, len(found_transactions))
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


def expenses_by_category(
    df: pd.DataFrame,
    category: str,
    reference_date: str
) -> str:
    """Функция отчёта «Траты по категории»."""
    try:
        logger.info(f"Запуск отчёта 'Траты по категории' для категории '{category}' с датой отсчёта {reference_date}")
        ref_date = datetime.strptime(reference_date, '%Y-%m-%d')
        start_date = ref_date - timedelta(days=90)

        required_columns = ['date', 'amount', 'category']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"В DataFrame отсутствуют необходимые колонки: {missing_columns}"
            logger.error(error_msg)
            raise KeyError(error_msg)

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        filtered_df = df[
            (df['category'] == category) &
            (df['date'] >= start_date) &
            (df['date'] <= ref_date)
            ].copy()
        filtered_df.dropna(subset=['date'], inplace=True)

        if filtered_df.empty:
            logger.warning(f"Нет транзакций по категории '{category}' за период с {start_date.date()} по {ref_date.date()}")
            return _format_expenses_response([], category, reference_date, 0.0, 0)

        # Рассчитываем общую сумму трат
        total_amount = filtered_df['amount'].sum()

        # Группируем по месяцам и считаем сумму за каждый месяц
        monthly_expenses = filtered_df.groupby(
            filtered_df['date'].dt.to_period('M')
        )['amount'].sum().reset_index()

        # Форматируем данные для JSON
        monthly_data = []
        for _, row in monthly_expenses.iterrows():
            month_str = row['date'].strftime('%Y-%m')
            monthly_data.append({
                'month': month_str,
                'amount': float(row['amount'])
            })

        # Сортируем по дате (от старых к новым)
        monthly_data.sort(key=lambda x: x['month'])

        # Формируем итоговый JSON‑ответ
        result = _format_expenses_response(
            monthly_data,
            category,
            reference_date,
            float(total_amount),
            len(filtered_df)
        )
        logger.info(f"Отчёт успешно сформирован. Общая сумма трат: {total_amount}")
        return result

    except Exception as e:
        error_message = f"Ошибка в функции expenses_by_category: {str(e)}"
        logger.error(error_message)
        error_response = {
            "status": "error",
            "message": error_message,
            "category": category,
            "reference_date": reference_date,
            "total_amount": 0.0,
            "transaction_count": 0,
            "monthly_breakdown": []
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)
