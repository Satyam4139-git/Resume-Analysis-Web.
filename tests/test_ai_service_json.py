import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

sys.path.insert(0, PROJECT_ROOT)

from app.services.ai_service import AIService


def main():

    service = AIService()

    prompt = """
Return ONLY valid JSON.

{
    "message":"hello"
}
"""

    result = service.send_json_prompt(
        prompt
    )

    print("\n")
    print("=" * 80)
    print("FINAL PYTHON OBJECT")
    print("=" * 80)
    print(result)
    print(type(result))
    print("=" * 80)


if __name__ == "__main__":
    main()