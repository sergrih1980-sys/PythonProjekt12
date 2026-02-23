import json
import unittest
from unittest.mock import Mock, patch

from src.views import home_page


class TestHomePage(unittest.TestCase):

    @patch('src.views.fetch_external_data')
    @patch('src.views.process_data_with_pandas')
    @patch('src.views.format_response')
    def test_home_page_success(self, mock_format_response, mock_process_data, mock_fetch_data):
        # Подготовка моков
        mock_fetch_data.return_value = [{"id": 1, "value": "test"}]
        mock_processed_data = Mock()
        mock_process_data.return_value = mock_processed_data
        expected_response_dict = {"status": "success", "data": "processed"}
        mock_format_response.return_value = expected_response_dict

        test_date = "2024-01-15"

        # Выполнение
        result = home_page(test_date)

        # Проверки вызовов моков — с корректными параметрами
        mock_fetch_data.assert_called_once_with(
            "https://api.example.com/data",
            {"date": test_date}
        )
        mock_process_data.assert_called_once_with(mock_fetch_data.return_value)
        mock_format_response.assert_called_once_with(mock_processed_data, test_date)

        # Обрабатываем результат: JSON‑строка или dict
        if isinstance(result, str):
            result_dict = json.loads(result)
        else:
            result_dict = result

        self.assertEqual(result_dict, expected_response_dict)

    @patch('src.views.fetch_external_data')
    @patch('src.views.process_data_with_pandas')
    @patch('src.views.format_response')
    def test_home_page_api_failure_with_fallback(self, mock_format_response,
                                                 mock_process_data, mock_fetch_data):
        test_date = "2024-01-15"
        # Имитируем сбой API
        mock_fetch_data.return_value = None

        # Заглушка данных для fallback
        fallback_data = [
            {"id": 1, "value": "test1", "category": "A"},
            {"id": 2, "value": "test2", "category": "B"}
        ]

        mock_processed_data = Mock()
        mock_process_data.return_value = mock_processed_data
        expected_response_data = {"status": "success", "data": "fallback"}
        mock_format_response.return_value = expected_response_data

        # Выполнение
        result = home_page(test_date)

        # Проверяем вызовы моков — с корректными параметрами
        mock_fetch_data.assert_called_once_with(
            "https://api.example.com/data",
            {"date": test_date}
        )
        mock_process_data.assert_called_once_with(fallback_data)
        mock_format_response.assert_called_once_with(mock_processed_data, test_date)

        # Обрабатываем результат: JSON‑строка или dict
        if isinstance(result, str):
            result_dict = json.loads(result)
        else:
            result_dict = result

        self.assertEqual(result_dict, expected_response_data)

    @patch('src.views.fetch_external_data')
    @patch('src.views.process_data_with_pandas')
    @patch('src.views.format_response')
    def test_home_page_formatting_error(self, mock_format_response,
                                        mock_process_data, mock_fetch_data):
        mock_fetch_data.return_value = [{"id": 1}]
        mock_process_data.return_value = Mock()
        mock_format_response.side_effect = ValueError("Formatting error")

        result = home_page("2024-01-15")

        error_response = json.loads(result[0]) if isinstance(result, tuple) else json.loads(result)
        status_code = result[1] if isinstance(result, tuple) else 500

        self.assertEqual(status_code, 500)
        self.assertEqual(error_response["status"], "error")
        self.assertIn("Formatting error", error_response["message"])

    @patch('src.views.fetch_external_data')
    @patch('src.views.process_data_with_pandas')
    @patch('src.views.format_response')
    def test_home_page_general_exception(self, mock_format_response,
                                         mock_process_data, mock_fetch_data):
        mock_fetch_data.side_effect = Exception("General error")

        result = home_page("2024-01-15")

        error_response = json.loads(result[0]) if isinstance(result, tuple) else json.loads(result)
        status_code = result[1] if isinstance(result, tuple) else 500

        self.assertEqual(status_code, 500)
        self.assertEqual(error_response["status"], "error")
        self.assertIn("General error", error_response["message"])

    @patch('src.views.fetch_external_data')
    @patch('src.views.process_data_with_pandas')
    @patch('src.views.format_response')
    def test_home_page_processing_error(self, mock_format_response,
                                        mock_process_data, mock_fetch_data):
        mock_fetch_data.return_value = [{"id": 1}]
        mock_process_data.side_effect = ValueError("Processing error")

        result = home_page("2024-01-15")

        error_response = json.loads(result[0]) if isinstance(result, tuple) else json.loads(result)
        status_code = result[1] if isinstance(result, tuple) else 500

        self.assertEqual(status_code, 500)
        self.assertEqual(error_response["status"], "error")
        self.assertIn("Processing error", error_response["message"])