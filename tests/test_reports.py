import unittest
import json
from datetime import datetime, timedelta
import pandas as pd
from src.reports import expenses_by_category


class TestExpensesByCategory(unittest.TestCase):

    def setUp(self):
        """Подготовка тестовых данных перед каждым тестом."""
        self.test_df = pd.DataFrame({
            'date': [
                '2024-01-15',  # должна учитываться в 90‑дневном периоде
                '2024-02-20',
                '2024-03-10',
                '2024-04-05',
                '2024-05-12'
            ],
            'amount': [1000, 1500, 800, 2000, 1200],
            'category': [
                'Продукты',
                'Рестораны',
                'Продукты',
                'Транспорт',
                'Продукты'
            ]
        })
        self.reference_date = '2024-05-31'

    def test_expenses_by_category_success(self):
        """Тест успешного выполнения отчёта для категории 'Продукты'."""
        result = expenses_by_category(self.test_df, 'Продукты', self.reference_date)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["category"], "Продукты")
        self.assertEqual(response["reference_date"], "2024-05-31")

        # Расчёт period_start: 90 дней назад от reference_date
        ref_date = datetime.strptime(self.reference_date, '%Y-%m-%d')
        period_start = (ref_date - timedelta(days=90)).strftime('%Y-%m-%d')
        self.assertEqual(response["period_start"], period_start)
        self.assertEqual(response["period_end"], "2024-05-31")

        # Общая сумма: 1000 (янв) + 800 (мар) + 1200 (май) = 3000
        self.assertAlmostEqual(response["total_amount"], 3000.00, places=2)
        self.assertEqual(response["transaction_count"], 3)

        # Проверка ежемесячной разбивки
        monthly_breakdown = response["monthly_breakdown"]
        self.assertEqual(len(monthly_breakdown), 3)  # январь, март, май

        jan_data = next(item for item in monthly_breakdown if item["month"] == "2024-01")
        self.assertAlmostEqual(jan_data["amount"], 1000.00, places=2)

        march_data = next(item for item in monthly_breakdown if item["month"] == "2024-03")
        self.assertAlmostEqual(march_data["amount"], 800.00, places=2)

        may_data = next(item for item in monthly_breakdown if item["month"] == "2024-05")
        self.assertAlmostEqual(may_data["amount"], 1200.00, places=2)

    def test_expenses_by_category_invalid_date_format(self):
        """Тест неверного формата даты отсчёта."""
        with self.assertRaises(ValueError) as context:
            expenses_by_category(self.test_df, 'Продукты', '31-05-2024')

        self.assertIn("Неверный формат даты", str(context.exception))

    def test_expenses_by_category_incorrect_dates(self):
        """Тест обработки некорректных дат в DataFrame."""
        df_with_bad_dates = pd.DataFrame({
            'date': ['2024-01-15', 'некорректная дата', '2024-03-10'],
            'amount': [1000, 1500, 800],
            'category': ['Продукты', 'Продукты', 'Продукты']
        })

        result = expenses_by_category(df_with_bad_dates, 'Продукты', self.reference_date)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")

        # Должны остаться только корректные даты: январь (1000) и март (800)
        self.assertAlmostEqual(response["total_amount"], 1800.00, places=2)
        self.assertEqual(response["transaction_count"], 2)

        # Проверка ежемесячной разбивки для корректных дат
        monthly_breakdown = response["monthly_breakdown"]
        self.assertEqual(len(monthly_breakdown), 2)  # январь и март

        jan_data = next((item for item in monthly_breakdown if item["month"] == "2024-01"), None)
        self.assertIsNotNone(jan_data)
        self.assertAlmostEqual(jan_data["amount"], 1000.00, places=2)

        march_data = next((item for item in monthly_breakdown if item["month"] == "2024-03"), None)
        self.assertIsNotNone(march_data)
        self.assertAlmostEqual(march_data["amount"], 800.00, places=2)

    def test_expenses_by_category_no_matching_transactions(self):
        """Тест отсутствия транзакций по категории в периоде."""
        result = expenses_by_category(self.test_df, 'Одежда', self.reference_date)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["total_amount"], 0.00)
        self.assertEqual(response["transaction_count"], 0)
        self.assertEqual(len(response["monthly_breakdown"]), 0)

    def test_expenses_by_category_empty_dataframe(self):
        """Тест с пустым DataFrame."""
        empty_df = pd.DataFrame(columns=['date', 'amount', 'category'])
        result = expenses_by_category(empty_df, 'Продукты', self.reference_date)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["total_amount"], 0.00)
        self.assertEqual(response["transaction_count"], 0)
        self.assertEqual(len(response["monthly_breakdown"]), 0)