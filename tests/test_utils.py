import unittest
from unittest.mock import Mock, patch
from requests.exceptions import HTTPError, RequestException

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
        # Имитируем сетевую ошибку
        mock_get.side_effect = RequestException("Connection failed")

        # Функция должна вернуть None при сетевой ошибке
        result = fetch_external_data("2024-01-15")
        self.assertIsNone(result)

    @patch('requests.get')
    def test_fetch_external_data_http_error(self, mock_get):
        # Имитируем HTTP-ошибку (4xx/5xx)
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        # Вызываем raise_for_status вручную для имитации поведения requests
        with patch.object(mock_response, 'raise_for_status', side_effect=HTTPError("404 Not Found")):
            # Функция должна вернуть None при HTTP-ошибке
            result = fetch_external_data("2024-01-15")
            self.assertIsNone(result)

    @patch('requests.get')
    def test_fetch_external_data_json_decode_error(self, mock_get):
        # Сервер возвращает не-JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Invalid JSON"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        # Функция должна вернуть None при ошибке декодирования
        result = fetch_external_data("2024-01-15")
        self.assertIsNone(result)
