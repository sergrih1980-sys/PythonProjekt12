import unittest
from unittest.mock import patch, Mock
import requests
from requests.exceptions import RequestException
from src.utils import fetch_external_data


class TestUtilsFunctions(unittest.TestCase):

    @patch('requests.get')
    def test_fetch_external_data_success(self, mock_get):
        # Подготовка
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        # Выполнение
        result = fetch_external_data("2024-01-15")

        # Проверки
        self.assertEqual(result, {"data": "test"})
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_fetch_external_data_request_error(self, mock_get):
        # Подготовка: имитируем ошибку запроса (например, сетевые проблемы)
        mock_get.side_effect = RequestException("Connection failed")

        # Выполнение
        with self.assertRaises(RequestException) as context:
            fetch_external_data("2024-01-15")

        # Проверка сообщения исключения
        self.assertIn("Connection failed", str(context.exception))

    @patch('requests.get')
    def test_fetch_external_data_http_error(self, mock_get):
        # Подготовка: имитируем HTTP‑ошибку (4xx/5xx)
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        # Выполнение
        with self.assertRaises(requests.exceptions.HTTPError) as context:
            fetch_external_data("2024-01-15")

        # Проверка сообщения
        self.assertIn("404 Not Found", str(context.exception))

    @patch('requests.get')
    def test_fetch_external_data_json_decode_error(self, mock_get):
        # Подготовка: сервер возвращает не‑JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Invalid JSON"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        # Выполнение
        result = fetch_external_data("2024-01-15")

        # Ожидаем None при ошибке декодирования
        self.assertIsNone(result)
