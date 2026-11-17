import os
import unittest
from unittest.mock import Mock, patch

from buscador_de_patentes.api import getPatentes


class GetPatentesTests(unittest.TestCase):
    @patch.dict(os.environ, {"API_KEY": "test-key"})
    @patch("buscador_de_patentes.api.requests.post")
    def test_api_error_is_reported_instead_of_format_error(self, post):
        response = Mock()
        response.json.return_value = {
            "status": False,
            "error_code": "INVALID_QUERY",
            "error_msg": "Consulta inválida",
        }
        post.return_value = response

        with self.assertRaisesRegex(
            ValueError, "INVALID_QUERY.*Consulta inválida"
        ):
            getPatentes("termo")

    @patch.dict(os.environ, {"API_KEY": "test-key"})
    @patch("buscador_de_patentes.api.requests.post")
    def test_successful_response_returns_results(self, post):
        resultados = [{"pn": "BR123"}]
        response = Mock()
        response.json.return_value = {
            "status": True,
            "data": {"results": resultados},
        }
        post.return_value = response

        self.assertEqual(getPatentes("termo"), resultados)


if __name__ == "__main__":
    unittest.main()
