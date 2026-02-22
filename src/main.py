import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === ФУНКЦИИ ОТЧЁТА «ТРАТЫ ПО КАТЕГОРИИ» ===


def expenses_by_category(
    df: pd.DataFrame,
    category: str,
    reference_date: str
) -> str:
    """
    Функция отчёта «Траты по категории».
    """
    try:
        logger.info("Запуск отчёта 'Траты по категории' для категории '%s' \
        с датой отсчёта %s" ,category,
        reference_date)

        # Парсим дату отсчёта
        try:
            ref_date = datetime.strptime(reference_date, '%Y-%m-%d')
        except ValueError as e:
            error_msg = "Неверный формат даты отсчёта. Ожидаемый формат: YYYY-MM-DD. Получено: %s" % reference_date
            logger.error(error_msg)
            raise ValueError(error_msg) from e

        # Определяем начало трёхмесячного периода
        start_date = ref_date - timedelta(days=90)

        # Проверяем наличие необходимых колонок в DataFrame
        required_columns = ['date', 'amount', 'category']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = "В DataFrame отсутствуют необходимые колонки: %s" % missing_columns
            logger.error(error_msg)
            raise KeyError(error_msg)

        # Преобразуем колонку 'date' в datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Фильтруем данные
        filtered_df = df[
            (df['category'] == category) &
            (df['date'] >= start_date) &
            (df['date'] <= ref_date)
        ].copy()

        # Удаляем строки с некорректными датами
        filtered_df.dropna(subset=['date'], inplace=True)

        # Если нет данных по категории за период
        if filtered_df.empty:
            logger.warning = ("Нет транзакций по категории '%s' за период с %s по %s", category,
            start_date.date(), ref_date.date())
            return _format_expenses_response([], category, reference_date, 0.0, 0)

        # Рассчитываем общую сумму трат
        total_amount = filtered_df['amount'].sum()

        # Группируем по месяцам
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

        # Сортируем по дате
        monthly_data.sort(key=lambda x: x['month'])

        # Формируем итоговый JSON‑ответ
        result = _format_expenses_response(
            monthly_data,
            category,
            reference_date,
            float(total_amount),
            len(filtered_df)
        )
        logger.info("Отчёт успешно сформирован. Общая сумма трат: %s", total_amount)
        return result

    except Exception as e:
        error_message = "Ошибка в функции expenses_by_category: %s" % str(e)
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


def _format_expenses_response(
    monthly_data: list,
    category: str,
    reference_date: str,
    total_amount: float,
    transaction_count: int
) -> str:
    """Вспомогательная функция для формирования JSON‑ответа (траты по категории)."""
    response = {
        "status": "success",
        "category": category,
        "reference_date": reference_date,
        "period_start": (datetime.strptime(reference_date, '%Y-%m-%d') - timedelta(days=90)).strftime('%Y-%m-%d'),
        "period_end": reference_date,
        "total_amount": round(total_amount, 2),
        "transaction_count": transaction_count,
        "monthly_breakdown": monthly_data
    }
    return json.dumps(response, ensure_ascii=False, indent=2)

# === ФУНКЦИИ «ПРОСТОГО ПОИСКА» ===


def simple_search(search_query: str, transactions: List[Dict[str, Any]]) -> str:
    """Функция сервиса «Простой поиск»."""
    try:
        logger.info("Запуск поиска с запросом: '%s'", search_query)

        # Нормализуем поисковый запрос
        normalized_query = search_query.strip().lower()

        if not normalized_query:
            logger.warning("Получен пустой поисковый запрос")
            return _format_search_response([], search_query, 0)

        # Список для хранения найденных транзакций
        found_transactions = []

        # Перебираем все транзакции и ищем совпадения
        for transaction in transactions:
            match_found = False
            for key, value in transaction.items():
                if isinstance(value, str):
                    if normalized_query in value.lower():
                        match_found = True
                        break
            if match_found:
                found_transactions.append(transaction)

        # Формируем JSON‑ответ
        result = _format_search_response(found_transactions, search_query, len(found_transactions))
        logger.info("Поиск завершён. Найдено %d транзакций", len(found_transactions))
        return result

    except Exception as e:
        error_message = "Ошибка в функции simple_search: %s" % str(e)
        logger.error(error_message)
        error_response = {
            "status": "error",
            "message": error_message,
            "search_query": search_query,
            "found_count": 0,
            "results": []
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)


def _format_search_response(results: List[Dict[str, Any]], query: str, count: int) -> str:
    """Вспомогательная функция для формирования JSON‑ответа (поиск)."""
    response = {
        "status": "success",
        "search_query": query,
        "found_count": count,
        "results": results
    }
    return json.dumps(response, ensure_ascii=False, indent=2)


# === ФУНКЦИИ ГЛАВНОЙ СТРАНИЦЫ ===

def parse_datetime(date_string: str) -> datetime:
    """Парсит строку даты и времени в объект datetime."""
    try:
        parsed_date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        logger.info("Успешно распарсена дата: %s", date_string)
        return parsed_date
    except ValueError as e:
        logger.error("Ошибка парсинга даты %s: %s", date_string, e)
        raise ValueError("Неверный формат даты. Ожидаемый формат: YYYY-MM-DD HH:MM:SS")


def fetch_external_data(api_url: str, params: Dict = None) -> Dict:
    """Получает данные из внешнего API."""
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Успешно получены данные из API: %s", api_url)
        return data

    except requests.exceptions.RequestException as e:
        error_msg = f"Ошибка при запросе к API {api_url}: {str(e)}"
        logger.error(error_msg)
        raise ConnectionError(error_msg) from e

    except json.JSONDecodeError as e:
        error_msg = f"Ошибка парсинга JSON от API {api_url}: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    except Exception as e:
        error_msg = f"Неожиданная ошибка при работе с API {api_url}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
