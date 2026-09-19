import unittest
from unittest.mock import patch

from src.mcp_server import ToolError
from src.mcp_server.providers import search_places
from src.observability import get_callback_handler


class RuntimeFallbackTests(unittest.TestCase):
    def test_search_places_uses_demo_data_when_api_key_is_invalid(self):
        with patch("src.mcp_server.providers.get_json", side_effect=ToolError("401 Unauthorized")):
            result = search_places("Tokyo", ["food", "history"], limit=3)

        self.assertEqual(result["city"], "Tokyo")
        self.assertTrue(result["places"])
        self.assertTrue(result["places"][0]["name"])

    def test_get_callback_handler_initializes_langfuse(self):
        with patch.dict("os.environ", {
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://cloud.langfuse.com",
        }, clear=False):
            with patch("langfuse.get_client", return_value=None), \
                 patch("langfuse.Langfuse") as langfuse_init, \
                 patch("langfuse.langchain.CallbackHandler") as callback_cls:
                handler = get_callback_handler()

        self.assertIsNotNone(handler)
        langfuse_init.assert_called_once()
        callback_cls.assert_called_once()


if __name__ == "__main__":
    unittest.main()
