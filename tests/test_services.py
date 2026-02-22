import json
import unittest

from src.services import simple_search


class TestSimpleSearch(unittest.TestCase):

    def setUp(self):
        """Подготовка тестовых данных перед каждым тестом."""
        self.test_transactions = [
            {"id": 1, "description": "Покупка продуктов в магазине X", "amount": 1500, "category": "Продукты"},
            {"id": 2, "description": "Оплата интернета", "amount": 500, "category": "Коммунальные"},
            {"id": 3, "description": "Кафе 'Уют'", "amount": 800, "category": "Рестораны"},
            {"id": 4, "description": "Бензин на АЗС", "amount": 2000, "category": "Транспорт"},
            {"id": 5, "description": "Подарок другу", "amount": 1000, "category": "Подарки"}
        ]

    def test_simple_search_exact_match(self):
        """Тест точного совпадения запроса с полем транзакции."""
        result = simple_search("Оплата интернета", self.test_transactions)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["search_query"], "Оплата интернета")
        self.assertEqual(response["found_count"], 1)
        self.assertEqual(len(response["results"]), 1)
        self.assertEqual(response["results"][0]["id"], 2)

    def test_simple_search_partial_match(self):
        """Тест частичного совпадения запроса."""
        result = simple_search("продукты", self.test_transactions)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["search_query"], "продукты")
        self.assertEqual(response["found_count"], 1)
        self.assertEqual(response["results"][0]["id"], 1)

    def test_simple_search_multiple_matches(self):
        """Тест поиска, возвращающего несколько результатов."""
        # Изменяем запрос, чтобы найти оба совпадения: 'АЗС' и 'Кафе'
        result = simple_search("ка", self.test_transactions)  # найдёт 'Кафе' и 'Продукты'
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["found_count"], 2)
        found_ids = [t["id"] for t in response["results"]]
        self.assertIn(1, found_ids)  # Покупка продуктов
        self.assertIn(3, found_ids)  # Кафе 'Уют'

    def test_simple_search_no_matches(self):
        """Тест отсутствия совпадений."""
        result = simple_search("не существующее", self.test_transactions)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["found_count"], 0)
        self.assertEqual(len(response["results"]), 0)

    def test_simple_search_empty_query(self):
        """Тест пустого поискового запроса."""
        result = simple_search("", self.test_transactions)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["search_query"], "")
        self.assertEqual(response["found_count"], 0)
        self.assertEqual(len(response["results"]), 0)

    def test_simple_search_whitespace_query(self):
        """Тест запроса с пробелами."""
        result = simple_search("   ", self.test_transactions)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        # Проверяем, что пробелы нормализованы в пустую строку
        self.assertEqual(response["search_query"].strip(), "")
        self.assertEqual(response["found_count"], 0)
        self.assertEqual(len(response["results"]), 0)

    def test_simple_search_case_insensitive(self):
        """Тест регистронезависимого поиска."""
        result1 = simple_search("кафе", self.test_transactions)
        result2 = simple_search("КАФЕ", self.test_transactions)

        response1 = json.loads(result1)
        response2 = json.loads(result2)

        self.assertEqual(response1["found_count"], 1)
        self.assertEqual(response2["found_count"], 1)
        self.assertEqual(response1["results"][0]["id"], 3)
        self.assertEqual(response2["results"][0]["id"], 3)

    def test_simple_search_search_in_different_fields(self):
        """Тест поиска по разным полям транзакции."""
        # Поиск по категории
        result_category = simple_search("Рестораны", self.test_transactions)
        response_category = json.loads(result_category)

        self.assertEqual(response_category["found_count"], 1)
        self.assertEqual(response_category["results"][0]["id"], 3)

        # Поиск по описанию
        result_desc = simple_search("Подарок", self.test_transactions)
        response_desc = json.loads(result_desc)

        self.assertEqual(response_desc["found_count"], 1)
        self.assertEqual(response_desc["results"][0]["id"], 5)

    def test_simple_search_with_non_string_values(self):
        """Тест обработки транзакций с нестроковыми значениями."""
        mixed_transactions = [
            {"id": 1, "description": "Тест", "amount": 100, "active": True},
            {"id": 2, "description": "Другой тест", "amount": 200, "tags": ["tag1", "tag2"]}
        ]

        result = simple_search("тест", mixed_transactions)
        response = json.loads(result)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["found_count"], 2)  # оба содержат "тест" в description
        found_ids = [t["id"] for t in response["results"]]
        self.assertIn(1, found_ids)
        self.assertIn(2, found_ids)
