import json
import re


class JSONExtractor:
    """
    Extracts JSON safely from AI responses.
    """


    @staticmethod
    def extract(response: str):

        if not response:
            raise ValueError(
                "Empty AI response"
            )


        response = response.strip()


        # Remove markdown
        response = re.sub(
            r"```json",
            "",
            response,
            flags=re.IGNORECASE
        )

        response = re.sub(
            r"```",
            "",
            response
        )


        response = response.strip()


        try:
            return json.loads(response)

        except json.JSONDecodeError as error:
            # Adding a closing brace to a truncated response cannot restore an
            # unfinished string, array, or missing value.  Reject it so callers
            # can return a clear model-response error instead of corrupted data.
            raise ValueError(
                "AI response did not contain complete valid JSON."
            ) from error



    @staticmethod
    def repair_json(text):

        """
        Repairs truncated JSON.
        """


        text = text.strip()


        # If object is opened but not closed
        if text.count("{") > text.count("}"):

            text += "}"


        # Remove trailing comma

        text = re.sub(
            r",\s*}",
            "}",
            text
        )


        return text
