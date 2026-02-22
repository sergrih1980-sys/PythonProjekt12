import unittest
from unittest.mock import patch, Mock
import json

from src.views import home_page


class TestHomePage(unittest.TestCase):

    @patch('src.views.parse_datetime')
    @patch('src.views.fetch_external_data')
    @patch('src.views.process_data_with_pandas')
    @patch('src.views.format_response')
    def test_home_page_success(self, mock_format_response, mock_process_data,
                              mock_fetch_data, mock_parse_datetime):
        """Тест успешного выполнения home_page."""
        # Подготавливаем тестовые данные
        test_date = "2024-01-15"
        mock_parsed_date = Mock()
        mock_raw_data = [{"id": 1, "value": "test", "category": "A"}]
        mock_processed_data = Mock()
        expected_response_data = {"status": "success", "data": "test"}

        # Настраиваем моки
        mock_parse_datetime.return_value = mock_parsed_date
        mock_fetch_data.return_value = mock_raw_data
        mock_process_data.return_value = mock_processed_data
        mock_format_response.return_value = expected_response_data

        # Вызываем функцию
        result = home_page(test_date)

        # Проверяем вызовы моков
        mock_parse_datetime.assert_called_once_with(test_date)
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

    @patch('src.views.parse_datetime')
    @patch('src.views.fetch_external_data')
    @patch('src.views.process_data_with_pandas')
    @patch('src.views.format_response')
    def test_home_page_api_failure_with_fallback(self, mock_format_response,
                                                         mock_process_data,
                                                         mock_fetch_data,
                                                         mock_parse_datetime):
        """Тест с откатом на заглушку при ошибке API (raw_data is None)."""
        test_date = "2024-01-15"

        # Мок возвращает None (ошибка API)
        mock_fetch_data.return_value = None

        # Остальные моки
        mock_parsed_date = Mock()
        mock_parse_datetime.return_value = mock_parsed_date

        mock_processed_data = Mock()
        mock_process_data.return_value = mock_processed_data

        expected_response_data = {"status": "success", "data": "fallback"}
        mock_format_response.return_value = expected_response_data

        result = home_page(test_date)

        # Проверяем, что использовали заглушку
        mock_process_data.assert_called_once()

        # Проверяем результат
        expected_json = json.dumps(
            expected_response_data, ensure_ascii=False, indent=2
        )
        self.assertEqual(result, expected_json)

    @patch('src.views.parse_datetime')
    @patch('src.views.fetch_external_data')
    @patch('src.views.process_data_with_pandas')
    @patch('src.views.format_response')
    def test_home_page_parse_error(self, mock_format_response, mock_process_data,
                          mock_fetch_data, mock_parse_datetime):
        """Тест ошибки парсинга даты."""
        test_date = "invalid-date"

        # Мок выбрасывает исключение
        mock_parse_datetime.side_effect = ValueError("Invalid date format")

        result = home_page(test_date)

        # Разбираем результат (кортеж: JSON, статус)
        error_json, status_code = result
        error_response = json.loads(error_json)

        # Проверяем ответ об ошибке
        self.assertEqual(error_response["status"], "error")
        self.assertIn("Invalid date format", error_response["message"])
        self.assertEqual(error_response["input_date"], test_date)
        self.assertEqual(status_code, 500)

    @patch('src.views.parse_datetime')
    @patch('src.views.fetch_external_data')
    @patch('src.views.process_data_with_pandas')
    @patch('src.views.format_response')
    def test_home_page_processing_error(self, mock_format_response,
                                     mock_process_data, mock_fetch_data,
                             mock_parse_datetime):
        """Тест ошибки обработки данных (process_data_with_pandas)."""
        test_date = "2024-01-15"

        # Все шаги до обработки проходят успешно
        mock_parsed_date = Mock()
        mock_parse_datetime.return_value = mock_parsed_date
        mock_raw_data = [{"id": 1}]
        mock_fetch_data.return_value = mock_raw_data

        # Мок обработки данных выбрасывает исключение
        mock_process_data.side_effect = Exception("Processing failed")

        result = home_page(test_date)

        error_json, status_code = result
        error_response = json.loads(error_json)

        self.assertEqual(error_response["status"], "error")
        self.assertIn("Processing failed", error_response["message"])
        self.assertEqual(status_code, 500)

    @patch('src.views.parse_datetime')
    @patch('src.views.fetch_external_data')
    @patch('src.views.process_data_with_pandas')
    @patch('src.views.format_response')
    def test_home_page_formatting_error(self, mock_format_response,
                             mock_process_data, mock_fetch_data,
             mock_parse_datetime):
        """Тест ошибки форматирования ответа (format_response)."""
        test_date = "2024-01-15"

        # Успешные шаги
        mock_parsed_date = Mock()
        mock_parse_datetime.return_value = mock_parsed_date
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
        self.assertEqual(status_code, 50