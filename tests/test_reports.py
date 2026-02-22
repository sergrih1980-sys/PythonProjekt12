import json
import unittest

import pandas as pd

from src.reports import expenses_by_category


class TestExpensesByCategory(unittest.TestCase):

    def setUp(self):
        """Подготовка тестовых данных перед каждым тестом."""
        # Создаём тестовый DataFrame с транзакциями
        self.test_df = pd.DataFrame({
            'date': [
                '2024-01-15',
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

        # Дата отсчёта для тестов
        self.reference_date = '2024-05-31'

    def test_expenses_by_category_success(self):
        """Тест успешного выполнения отчёта для категории 'Продукты'."""
        result = expenses_by_category(self.test_df, 'Продукты', self.reference_date)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["category"], "Продукты")
        self.assertEqual(response["reference_date"], "2024-05-31")
        self.assertEqual(response["period_start"], "2024-02-29")  # 90 дней назад
        self.assertEqual(response["period_end"], "2024-05-31")

        # Проверяем общую сумму (800 + 1200 = 2000)
        self.assertAlmostEqual(response["total_amount"], 2000.00, places=2)
        self.assertEqual(response["transaction_count"], 2)

        # Проверяем ежемесячную разбивку
        monthly_breakdown = response["monthly_breakdown"]
        self.assertEqual(len(monthly_breakdown), 2)  # два месяца: март и май

        # Март
        march_data = next(item for item in monthly_breakdown if item["month"] == "2024-03")
        self.assertAlmostEqual(march_data["amount"], 800.00, places=2)

        # Май
        may_data = next(item for item in monthly_breakdown if item["month"] == "2024-05")
        self.assertAlmostEqual(may_data["amount"], 1200.00, places=2)

    def test_expenses_by_category_no_data_for_category(self):
        """Тест отсутствия транзакций по указанной категории."""
        result = expenses_by_category(self.test_df, 'Одежда', self.reference_date)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["category"], "Одежда")
        self.assertEqual(response["total_amount"], 0.0)
        self.assertEqual(response["transaction_count"], 0)
        self.assertEqual(len(response["monthly_breakdown"]), 0)

    def test_expenses_by_category_invalid_date_format(self):
        """Тест неверного формата даты отсчёта."""
        with self.assertRaises(ValueError) as context:
            expenses_by_category(self.test_df, 'Продукты', '31-05-2024')

        self.assertIn("Неверный формат даты отсчёта", str(context.exception))

    def test_expenses_by_category_missing_columns(self):
        """Тест отсутствия необходимых колонок в DataFrame."""
        # DataFrame без колонки 'category'
        incomplete_df = self.test_df.drop('category', axis=1)

        result = expenses_by_category(incomplete_df, 'Продукты', self.reference_date)
        response = json.loads(result)

        self.assertEqual(response["status"], "error")
        self.assertIn("В DataFrame отсутствуют необходимые колонки", response["message"])

    def test_expenses_by_category_empty_dataframe(self):
        """Тест с пустым DataFrame."""
        empty_df = pd.DataFrame(columns=['date', 'amount', 'category'])

        result = expenses_by_category(empty_df, 'Продукты', self.reference_date)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["total_amount"], 0.0)
        self.assertEqual(response["transaction_count"], 0)
        self.assertEqual(len(response["monthly_breakdown"]), 0)

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
        # Должна остаться только одна корректная транзакция (2024-03-10)
        self.assertAlmostEqual(response["total_amount"], 800.00, places=2)
        self.assertEqual(response["transaction_count"], 1)
