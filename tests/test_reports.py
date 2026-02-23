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

        # Исправленная сумма: 800 (мар) + 1200 (май) = 2000
        self.assertAlmostEqual(response["total_amount"], 2000.00, places=2)
        self.assertEqual(response["transaction_count"], 2)  # Теперь 2 транзакции

        monthly_breakdown = response["monthly_breakdown"]
        self.assertEqual(len(monthly_breakdown), 2)  # март и май

        march_data = next((item for item in monthly_breakdown if item["month"] == "2024-03"), None)
        self.assertIsNotNone(march_data)
        self.assertAlmostEqual(march_data["amount"], 800.00, places=2)

        may_data = next((item for item in monthly_breakdown if item["month"] == "2024-05"), None)
        self.assertIsNotNone(may_data)
        self.assertAlmostEqual(may_data["amount"], 1200.00, places=2)