import json
import logging
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    date: Optional[str] = None
) -> pd.DataFrame:
    """
    Возвращает траты по заданной категории за последние три месяца.

    Args:
        transactions: DataFrame с транзакциями (должен содержать колонки 'date', 'amount', 'category')
        category: название категории для фильтрации
        date: опциональная дата в формате 'YYYY-MM-DD' (если не указана, берётся текущая дата)

    Returns:
        DataFrame с отфильтрованными транзакциями
    """
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

    Args:
        input_date_string: строка с датой и временем в формате 'YYYY-MM-DD HH:MM:SS'

    Returns:
        JSON-строка с полным ответом согласно ТЗ
    """
    try:
        # Парсим входную дату
        input_datetime = datetime.strptime(input_date_string, '%Y-%m-%d %H:%M:%S')
        hour = input_datetime.hour

        # Приветствие
        greeting = get_greeting(hour)

        # Пример данных для демонстрации (в реальной реализации нужно получать из API)
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
