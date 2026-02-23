import pandas as pd
from datetime import datetime, timedelta
import json

def expenses_by_category(df, category, reference_date):
    """
    Формирует отчёт по расходам для указанной категории за последние 90 дней.

    Args:
        df (pd.DataFrame): DataFrame с колонками 'date', 'amount', 'category'
        category (str): Категория для анализа
        reference_date (str): Дата отсчёта в формате 'YYYY-MM-DD'

    Returns:
        str: JSON‑строка с результатами отчёта
    """
    try:
        # Проверка формата даты отсчёта
        try:
            ref_date = datetime.strptime(reference_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Неверный формат даты отсчёта. Ожидаемый формат: YYYY-MM-DD")

        period_start = ref_date - timedelta(days=90)

        # Преобразование столбца date в datetime с обработкой ошибок
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Фильтрация: корректные даты, в периоде, по категории
        filtered_df = df[
            (df['date'].notna()) &
            (df['date'] >= period_start) &
            (df['date'] <= ref_date) &
            (df['category'] == category)
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

        # Расчёт общей суммы
        total_amount = float(filtered_df['amount'].sum())

        # Группировка по месяцам
        monthly_breakdown = []
        for month, group in filtered_df.groupby(filtered_df['date'].dt.to_period('M')):
            monthly_breakdown.append({
                "month": month.strftime('%Y-%m'),
                "amount": float(group['amount'].sum())
            })

        transaction_count = len(filtered_df)

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
        return json.dumps({
            "status": "error",
            "message": str(e)
        })