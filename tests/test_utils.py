import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import pandas as pd
from requests.exceptions import RequestException, HTTPError

from src.utils import (
    parse_datetime,
    fetch_external_data,
    process_data_with_pandas,
    format_response
)

class TestUtilsFunctions(unittest.TestCase):

    # --- Тесты для parse_datetime ---

    def test_parse_datetime_valid(self):
        """Тест успешного парсинга корректной даты."""
        result = parse_datetime("2024-01-15 14:30:00")
        expected = datetime(2024, 1, 15, 14, 30, 0)
        self.assertEqual(result, expected)

    def test_parse_datetime_invalid_format(self):
        """Тест обработки неверного формата даты."""
        with self.assertRaises(ValueError) as context:
            parse_datetime("15-01-2024 14:30:00")  # неверный порядок
        self.assertIn("Неверный формат даты", str(context.exception))

    def test_parse_datetime_empty_string(self):
        """Тест парсинга пустой строки."""
        with self.assertRaises(ValueError) as context:
            parse_datetime("")
        self.assertIn("Неверный формат даты", str(context.exception))

    def test_parse_datetime_wrong_separator(self):
        """Тест даты с неверными разделителями."""
        with self.assertRaises(ValueError) as context:
            parse_datetime("2024/01/15 14-30-00")
        self.assertIn("Неверный формат даты", str(context.exception))

    def test_parse_datetime_missing_time(self):
        """Тест даты без времени."""
        with self.assertRaises(ValueError) as context:
            parse_datetime("2024-01-15")
        self.assertIn("Неверный формат даты", str(context.exception))

    # --- Тесты для fetch_external_data ---

    @patch('requests.get')
    def test_fetch_external_data_success(self, mock_get):
        """Тест успешного получения данных."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        result = fetch_external_data("2024-01-15")

        self.assertEqual(result, {"data": "test"})
        mock_get.assert_called_once_with(
            "https://api.example.com/data",
            params={"date": "2024-01-15"},
            timeout=10
        )

    @patch('requests.get')
    def test_fetch_external_data_request_error(self, mock_get):
        """Тест обработки сетевой ошибки."""
        mock_get.side_effect = RequestException("Connection failed")
        result = fetch_external_data("2024-01-15")
        self.assertIsNone(result)

    @patch('requests.get')
    def test_fetch_external_data_http_error(self, mock_get):
        """Тест обработки HTTP-ошибки."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        result = fetch_external_data("2024-01-15")
        self.assertIsNone(result)

    @patch('requests.get')
    def test_fetch_external_data_json_decode_error(self, mock_get):
        """Тест обработки ошибки декодирования JSON."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Invalid JSON"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        result = fetch_external_data("2024-01-15")
        self.assertIsNone(result)

    @patch('requests.get')
    def test_fetch_external_data_timeout(self, mock_get):
        """Тест обработки таймаута."""
        mock_get.side_effect = RequestException("Timeout")
        result = fetch_external_data("2024-01-15")
        self.assertIsNone(result)

    # --- Тесты для process_data_with_pandas ---

    def test_process_data_with_pandas_empty(self):
        """Тест обработки пустых данных."""
        result = process_data_with_pandas([])
        self.assertEqual(result, [])

    def test_process_data_with_pandas_simple_data(self):
        """Тест обработки простых данных без timestamp и category."""
        raw_data = [
            {"id": 1, "value": "A"},
            {"id": 2, "value": "B"}
        ]
        result = process_data_with_pandas(raw_data)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 1)

    def test_process_data_with_pandas_with_timestamp(self):
        """Тест обработки данных с полем timestamp."""
        raw_data = [
            {"id": 1, "timestamp": "2024-01-15 10:00:00"},
            {"id": 2, "timestamp": "invalid-date"}
        ]
        result = process_data_with_pandas(raw_data)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 1)
        self.assertTrue(pd.isna(result[1]["timestamp"]))

    def test_process_data_with_pandas_with_category(self):
        """Тест агрегации по категориям."""
        raw_data = [
            {"category": "food", "amount": 100},
            {"category": "food", "amount": 200},
            {"category": "transport", "amount": 50}
        ]
        result = process_data_with_pandas(raw_data)
        self.assertEqual(len(result), 2)
        food_item = next(item for item in result if item["category"] == "food")
        transport_item = next(item for item in result if item["category"] == "transport")
        self.assertEqual(food_item["count"], 2)
        self.assertEqual(transport_item["count"], 1)

    def test_process_data_with_pandas_no_category_column(self):
        """Тест данных без колонки category."""
        raw_data = [
            {"name": "Item1", "price": 10.5},
            {"name": "Item2", "price": 20.0}
        ]
        result = process_data_with_pandas(raw_data)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Item1")

    # --- Тесты для format_response ---

    def test_format_response_simple_data(self):
        """Тест формирования ответа с простыми данными."""
        test_data = [{"id": 1}, {"id": 2}]
        result = format_response(test_data, "2024-01-15")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["input_date"], "2024-01-15")
        self.assertEqual(result["total_records"], 2)
        self.assertEqual(result["data"], test_data)

    def test_format_response_empty_data(self):
        """Тест формирования ответа с пустыми данными."""
        result = format_response([], "2024-01-15")
        self.assertEqual(result["total_records"], 0)
        self.assertEqual(result["data"], [])