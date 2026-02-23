from datetime import datetime, timedelta
import pandas as pd
import json

""" Траты по категориям """
def expenses_by_category(df, category, reference_date):
    # Валидация формата reference_date
    try:
        ref_date = datetime.strptime(reference_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Неверный формат даты отсчёта. Ожидаемый формат: YYYY-MM-DD")

    # Расчёт периода: 90 дней назад от reference_date
    period_start = ref_date - timedelta(days=90)

    # Конвертация дат в DataFrame с обработкой ошибок
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Фильтрация: только корректные даты в периоде и нужной категории
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

    # Суммирование по месяцам
    monthly_breakdown = []
    for month, group in filtered_df.groupby(filtered_df['date'].dt.to_period('M')):
        monthly_breakdown.append({
            "month": month.strftime('%Y-%m'),
            "amount": float(group['amount'].sum())
        })

    total_amount = float(filtered_df['amount'].sum())
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
