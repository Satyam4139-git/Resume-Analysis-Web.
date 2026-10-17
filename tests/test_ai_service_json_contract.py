import unittest
from types import SimpleNamespace

from app.exceptions.custom_exceptions import AIServiceError
from app.services.ai_service import AIService


class RecordingCompletions:
    def __init__(self, response):
        self.response = response
        self.request = None

    def create(self, **request):
        self.request = request
        return self.response


def response_with(content, finish_reason="stop"):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
                finish_reason=finish_reason,
            )
        ],
        model="test-model",
        usage=SimpleNamespace(),
    )


class AIServiceJSONContractTests(unittest.TestCase):
    def service_with(self, response):
        completions = RecordingCompletions(response)
        service = AIService()
        service.client = SimpleNamespace(
            chat=SimpleNamespace(completions=completions)
        )
        return service, completions

    def test_json_requests_disable_reasoning_and_enable_json_mode(self):
        service, completions = self.service_with(
            response_with('{"message":"ok"}')
        )

        self.assertEqual(service.send_json_prompt("Return JSON."), {"message": "ok"})
        self.assertEqual(
            completions.request["response_format"],
            {"type": "json_object"},
        )
        self.assertEqual(
            completions.request["extra_body"]["reasoning"],
            {"enabled": False},
        )

    def test_truncated_completion_is_rejected_before_json_decoding(self):
        service, _ = self.service_with(
            response_with('{"message":"unfinished', finish_reason="length")
        )

        with self.assertRaises(AIServiceError):
            service.send_json_prompt("Return JSON.")


if __name__ == "__main__":
    unittest.main()
