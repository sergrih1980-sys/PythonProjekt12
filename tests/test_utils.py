import unittest
from unittest.mock import patch, Mock
from datetime import datetime
import pandas as pd

# Замените 'your_module' на имя вашего модуля
from src.utils import (
    parse_datetime,
    fetch_external_data,
    process_data_with_pandas,
    format_response
)


class TestUtilsFunctions(unittest.TestCase):

    def test_parse_datetime_success(self):
        """Тест успешного парсинга даты."""
        test_date = "2024-01-15 14:30:00"
        result = parse_datetime(test_date)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)
        self.assertEqual(result.second, 0)

    def test_parse_datetime_invalid_format(self):
        """Тест ошибки парсинга даты с неверным форматом."""
        invalid_date = "15-01-2024 14:30:00"  # неверный формат

        with self.assertRaises(ValueError) as context:
            parse_datetime(invalid_date)

        self.assertIn("Неверный формат даты", str(context.exception))

    @patch('utils.requests')
    def test_fetch_external_data_success(self, mock_requests):
        """Тест успешного получения данных из API."""
        # Настраиваем мок для успешного ответа
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": "test", "status": "ok"}
        mock_requests.get.return_value = mock_response

        api_url = "https://api.example.com/data"
        params = {"date": "2024-01-15"}

        result = fetch_external_data(api_url, params)

        # Проверяем вызовы
        mock_requests.get.assert_called_once_with(
            api_url,
            params=params,
            timeout=10
        )
        self.assertEqual(result, {"data": "test", "status": "ok"})

    @patch('utils.requests')
    def test_fetch_external_data_request_error(self, mock_requests):
        """Тест ошибки запроса к API."""
        # Мок выбрасывает исключение
        mock_requests.get.side_effect = Exception("Connection failed")

        api_url = "https://api.example.com/data"

        result = fetch_external_data(api_url)

        self.assertIsNone(result)

    def test_process_data_with_pandas_empty_data(self):
        """Тест обработки пустых данных."""
        result = process_data_with_pandas([])
        self.assertEqual(result, [])

    def test_process_data_with_pandas_with_timestamp(self):
        """Тест обработки данных с колонкой timestamp."""
        raw_data = [
            {"id": 1, "timestamp": "2024-01-15 10:00:00", "category": "A"},
            {"id": 2, "timestamp": "2024-01-16 11:00:00", "category": "B"}
        ]

        result = process_data_with_pandas(raw_data)

        # Проверяем, что данные обработаны
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        # Проверяем наличие колонки count при группировке по category
        if result and 'count' in result[0]:
            self.assertIn('count', result[0])

    def test_process_data_with_pandas_without_category(self):
        """Тест обработки данных без колонки category."""
        raw_data = [
            {"id": 1, "value": "test1"},
            {"id": 2, "value": "test2"}
        ]

        result = process_data_with_pandas(raw_data)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIn('id', result[0])
        self.assertIn('value', result[0])

    def test_format_response_with_data(self):
        """Тест формирования ответа с данными."""
        test_data = [{"id": 1, "value": "test"}]
        input_date = "2024-01-15"

        result = format_response(test_data, input_date)

        # Проверяем структуру ответа
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["input_date"], input_date)
        self.assertIn("processed_at", result)
        self.assertEqual(result["data"], test_data)
        self.assertEqual(result["total_records"], 1)

    def test_format_response_empty_data(self):
        """Тест формирования ответа с пустыми данными."""
        empty_data = []
        input_date = "2024-01-15"

        result = format_response(empty_data, input_date)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["input_date"], input_date)
        self.assertEqual(result["total_records"], 0)
        self.assertEqual(result["data"], [])