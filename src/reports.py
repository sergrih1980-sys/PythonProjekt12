import json
import logging
from datetime import datetime, timedelta

import pandas as pd

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def expenses_by_category(
    df: pd.DataFrame,
    category: str,
    reference_date: str
) -> str:
    """
    Функция отчёта «Траты по категории».

    Принимает:
    - df (pd.DataFrame): DataFrame с транзакциями;
    - category (str): категория для анализа;
    - reference_date (str): дата отсчёта в формате 'YYYY-MM-DD' для трёхмесячного периода.

    Возвращает:
    - JSON‑строку с результатами анализа трат по категории за последние 3 месяца.
    """
    try:
        logger.info(f"Запуск отчёта 'Траты по категории' для категории '{category}' с датой отсчёта {reference_date}")

        # Парсим дату отсчёта
        try:
            ref_date = datetime.strptime(reference_date, '%Y-%m-%d')
        except ValueError as e:
            error_msg = f"Неверный формат даты отсчёта. Ожидаемый формат: YYYY-MM-DD. Получено: {reference_date}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

        # Определяем начало трёхмесячного периода
        start_date = ref_date - timedelta(days=90)

        # Проверяем наличие необходимых колонок в DataFrame
        required_columns = ['date', 'amount', 'category']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"В DataFrame отсутствуют необходимые колонки: {missing_columns}"
            logger.error(error_msg)
            raise KeyError(error_msg)

        # Преобразуем колонку 'date' в datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Фильтруем данные: только указанная категория и даты в трёхмесячном периоде
        filtered_df = df[
            (df['category'] == category) &
            (df['date'] >= start_date) &
            (df['date'] <= ref_date)
        ].copy()

        # Удаляем строки с некорректными датами
        filtered_df.dropna(subset=['date'], inplace=True)

        # Если нет данных по категории за период
        if filtered_df.empty:
            logger.warning(f"Нет транзакций по категории ' \
            {category}'за период с {start_date.date()} по {ref_date.date()}")
            return _format_response([], category, reference_date, 0.0, 0)

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
        result = _format_response(
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


def _format_response(
    monthly_data: list,
    category: str,
    reference_date: str,
    total_amount: float,
    transaction_count: int
) -> str:
    """
    Вспомогательная функция для формирования JSON‑ответа.
    """
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
