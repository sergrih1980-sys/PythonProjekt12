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

        ref_date = datetime.strptime(self.reference_date, '%Y-%m-%d')
        period_start = (ref_date - timedelta(days=90)).strftime('%Y-%m-%d')
        self.assertEqual(response["period_start"], period_start)
        self.assertEqual(response["period_end"], "2024-05-31")


        # Общая сумма: 1000 (янв) + 800 (мар) + 1200 (май) = 3000
        self.assertAlmostEqual(response["total_amount"], 3000.00, places=2)
        self.assertEqual(response["transaction_count"], 3)

        monthly_breakdown = response["monthly_breakdown"]
        self.assertEqual(len(monthly_breakdown), 3)  # январь, март, май

        jan_data = next((item for item in monthly_breakdown if item["month"] == "2024-01"), None)
        self.assertIsNotNone(jan_data)
        self.assertAlmostEqual(jan_data["amount"], 1000.00, places=2)