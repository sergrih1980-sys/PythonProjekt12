import json
import unittest
from unittest.mock import Mock, patch

from src.views import home_page


class TestHomePage(unittest.TestCase):

    @patch('src.utils.fetch_external_data')
    @patch('src.utils.process_data_with_pandas')
    @patch('src.utils.format_response')
    def test_home_page_success(self, mock_format_response, mock_process_data, mock_fetch_data):
        """Тест успешного выполнения home_page."""
        test_date = "2024-01-15"
        mock_raw_data = [
            {"id": 1, "value": "test1", "category": "A"},
            {"id": 2, "value": "test2", "category": "B"}
        ]
        mock_processed_data = Mock()
        expected_response_data = {"status": "success", "data": "test"}

        # Настраиваем моки
        mock_fetch_data.return_value = mock_raw_data
        mock_process_data.return_value = mock_processed_data
        mock_format_response.return_value = expected_response_data

        result = home_page(test_date)

        # Проверяем вызовы моков
        mock_fetch_data.assert_called_once_with(
            "https://api.example.com/data",
            {"date": test_date}
        )
        mock_process_data.assert_called_once_with(mock_raw_data)
        mock_format_response.assert_called_once_with(mock_processed_data, test_date)

        # Проверяем результат
        expected_json = json.dumps(
            expected_response_data, ensure_ascii=False, indent=2
        )
        self.assertEqual(result, expected_json)

    @patch('src.utils.fetch_external_data')
    @patch('src.utils.process_data_with_pandas')
    @patch('src.utils.format_response')
    def test_home_page_api_failure_with_fallback(self, mock_format_response,
                                                 mock_process_data,
                                                 mock_fetch_data):
        """Тест с откатом на заглушку при ошибке API (raw_data is None)."""
        test_date = "2024-01-15"

        # Мок возвращает None (ошибка API)
        mock_fetch_data.return_value = None

        # Заглушка данных
        fallback_data = [
            {"id": 1, "value": "test1", "category": "A"},
            {"id": 2, "value": "test2", "category": "B"}
        ]

        # Остальные моки
        mock_processed_data = Mock()
        mock_process_data.return_value = mock_processed_data

        expected_response_data = {"status": "success", "data": "fallback"}
        mock_format_response.return_value = expected_response_data

        result = home_page(test_date)

        # Проверяем, что fetch вернул None
        mock_fetch_data.assert_called_once()

        # Проверяем, что использовали заглушку и продолжили обработку
        mock_process_data.assert_called_once_with(fallback_data)
        mock_format_response.assert_called_once_with(mock_processed_data, test_date)

        # Проверяем результат
        expected_json = json.dumps(
            expected_response_data, ensure_ascii=False, indent=2
        )
        self.assertEqual(result, expected_json)

    @patch('src.utils.fetch_external_data')
    @patch('src.utils.process_data_with_pandas')
    @patch('src.utils.format_response')
    def test_home_page_processing_error(self, mock_format_response,
                                        mock_process_data, mock_fetch_data):
        """Тест ошибки обработки данных (process_data_with_pandas)."""
        test_date = "2024-01-15"

        # Все шаги до обработки проходят успешно
        mock_raw_data = [{"id": 1}]
        mock_fetch_data.return_value = mock_raw_data

        # Мок обработки данных выбрасывает исключение
        mock_process_data.side_effect = Exception("Processing failed")

        result = home_page(test_date)

        # Разбираем результат — в случае ошибки возвращается кортеж (JSON, статус)
        error_json, status_code = result
        error_response = json.loads(error_json)

        # Проверяем ответ об ошибке
        self.assertEqual(error_response["status"], "error")
        self.assertIn("Processing failed", error_response["message"])
        self.assertEqual(error_response["input_date"], test_date)
        self.assertEqual(status_code, 500)

    @patch('src.utils.fetch_external_data')
    @patch('src.utils.process_data_with_pandas')
    @patch('src.utils.format_response')
    def test_home_page_formatting_error(self, mock_format_response,
                                        mock_process_data, mock_fetch_data):
        """Тест ошибки форматирования ответа (format_response)."""
        test_date = "2024-01-15"

        # Успешные шаги
        mock_raw_data = [{"id": 1}]
        mock_fetch_data.return_value = mock_raw_data
        mock_processed_data = Mock()
        mock_process_data.return_value = mock_processed_data

        # Ошибка в форматировании
        mock_format_response.side_effect = Exception("Formatting failed")

        result = home_page(test_date)

        error_json, status_code = result
        error_response = json.loads(error_json)

        self.assertEqual(error_response["status"], "error")
        self.assertIn("Formatting failed", error_response["message"])
        self.assertEqual(status_code, 500)

    @patch('src.utils.fetch_external_data')
    @patch('src.utils.process_data_with_pandas')
    @patch('src.utils.format_response')
    def test_home_page_general_exception(self, mock_format_response,
                                         mock_process_data, mock_fetch_data):
        """Тест общей ошибки в функции."""
        test_date = "2024-01-15"

        # Мок fetch_external_data выбрасывает исключение
        mock_fetch_data.side_effect = Exception("API connection failed")

        result = home_page(test_date)

        error_json, status_code = result
        error_response = json.loads(error_json)

        self.assertEqual(error_response["status"], "error")
        self.assertIn("API connection failed", error_response["message"])
        self.assertEqual(error_response["input_date"], test_date)
        self.assertEqual(status_code, 500)
        # Проверяем, что последующие шаги не выполнялись
        mock_process_data.assert_not_called()
        mock_format_response.assert_not_called()
