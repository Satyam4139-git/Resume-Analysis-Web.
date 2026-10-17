"""
AI Service Layer
----------------
Centralized OpenRouter AI service for the Resume Analysis application.

Responsibilities:
- Send normal AI prompts
- Send JSON prompts
- Safely extract JSON
- Handle truncated / malformed JSON
- Handle OpenRouter model failures
- Automatically switch between models
- Handle reasoning requirements
- Retry recoverable failures
- Never return empty successful responses
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.core.config import (
    OPENROUTER_API_KEY,
    BASE_URL,
    MODEL_NAME,
    MAX_OUTPUT_TOKENS,
    TEMPERATURE,
)

from app.exceptions.custom_exceptions import AIServiceError


logger = logging.getLogger("ResumeAnalyzer")


class AIService:
    """
    Centralized OpenRouter AI service.

    Primary model:
        MODEL_NAME from configuration

    Fallback:
        openrouter/free
    """

    def __init__(self):

        self.model = MODEL_NAME

        self.fallback_models: List[str] = [
            "openrouter/free",
        ]

        self.max_output_tokens = MAX_OUTPUT_TOKENS
        self.temperature = TEMPERATURE

        if not OPENROUTER_API_KEY:
            raise AIServiceError(
                "OPENROUTER_API_KEY is missing. "
                "Please check your .env file."
            )

        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=BASE_URL,
            max_retries=0,
            # The SDK default waits up to 10 minutes on a slow free model.
            timeout=float(os.getenv("AI_TIMEOUT_SECONDS", "25")),
        )

        logger.info(
            "AI Service initialized using model: %s",
            self.model,
        )

        logger.info(
            "Default maximum output tokens: %s",
            self.max_output_tokens,
        )

        logger.info(
            "AI fallback models: %s",
            self.fallback_models,
        )

    # =========================================================
    # ERROR CLASSIFICATION
    # =========================================================

    @staticmethod
    def _is_fallback_error(error: Exception) -> bool:
        """
        Determine whether another model should be tried.
        """

        message = str(error).lower()

        recoverable_markers = [
            "400",
            "401",
            "404",
            "408",
            "409",
            "429",
            "500",
            "502",
            "503",
            "504",

            "rate limit",
            "rate-limited",
            "too many requests",

            "not found",
            "no endpoints found",
            "model is unavailable",
            "endpoint is unavailable",
            "no endpoint",

            "bad gateway",
            "service unavailable",
            "gateway timeout",
            "upstream error",
            "upstream unavailable",
            "temporarily unavailable",
            "temporarily overloaded",
            "overloaded",

            "reasoning is mandatory",
            "cannot be disabled",
            "invalid reasoning",
            "unsupported parameter",

            "timed out",
            "timeout",
            "connection error",

            "empty response",
            "empty content",
            "blank content",
            "no choices",
        ]

        return any(
            marker in message
            for marker in recoverable_markers
        )

    # =========================================================
    # JSON EXTRACTION
    # =========================================================

    def _extract_json(
        self,
        content: str,
    ) -> Dict[str, Any]:
        """
        Extract a JSON object from an AI response.

        Handles:
        - pure JSON
        - markdown JSON
        - surrounding text
        - nested objects
        - escaped strings
        """

        if not content:
            raise AIServiceError(
                "AI response was empty."
            )

        content = str(content).strip()

        logger.info(
            "AI response received. length=%s",
            len(content),
        )

        logger.debug(
            "AI response:\n%s",
            content[:10000],
        )

        # -----------------------------------------------------
        # Remove markdown fences
        # -----------------------------------------------------

        cleaned = re.sub(
            r"```(?:json|JSON)?",
            "",
            content,
        )

        cleaned = cleaned.replace(
            "```",
            "",
        ).strip()

        # -----------------------------------------------------
        # Direct JSON
        # -----------------------------------------------------

        try:
            parsed = json.loads(cleaned)

            if isinstance(parsed, dict):
                return parsed

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            pass

        # -----------------------------------------------------
        # Balanced JSON extraction
        # -----------------------------------------------------

        for start in [
            match.start()
            for match in re.finditer(r"\{", cleaned)
        ]:

            depth = 0
            in_string = False
            escape = False

            for index in range(
                start,
                len(cleaned),
            ):

                char = cleaned[index]

                if escape:
                    escape = False
                    continue

                if char == "\\" and in_string:
                    escape = True
                    continue

                if char == '"':
                    in_string = not in_string
                    continue

                if in_string:
                    continue

                if char == "{":
                    depth += 1

                elif char == "}":
                    depth -= 1

                    if depth == 0:

                        candidate = cleaned[
                            start:index + 1
                        ].strip()

                        try:

                            parsed = json.loads(
                                candidate
                            )

                            if isinstance(
                                parsed,
                                dict,
                            ):
                                logger.info(
                                    "JSON extracted using "
                                    "balanced-brace extraction."
                                )

                                return parsed

                        except (
                            json.JSONDecodeError,
                            TypeError,
                        ):
                            break

        # -----------------------------------------------------
        # Regex fallback
        # -----------------------------------------------------

        matches = re.findall(
            r"\{[\s\S]*\}",
            cleaned,
        )

        for match in matches:

            try:

                parsed = json.loads(
                    match
                )

                if isinstance(
                    parsed,
                    dict,
                ):
                    return parsed

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                continue

        logger.error(
            "AI response could not be converted into JSON."
        )

        logger.error(
            "AI response length: %s",
            len(cleaned),
        )

        logger.error(
            "AI response preview:\n%s",
            cleaned[:5000],
        )

        raise AIServiceError(
            "AI response did not contain a valid JSON object."
        )

    # =========================================================
    # REQUEST BUILDER
    # =========================================================

    def _build_request(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        json_mode: bool,
    ) -> Dict[str, Any]:

        request_kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if json_mode:
            request_kwargs["response_format"] = {
                "type": "json_object"
            }

        # openrouter/free can route to reasoning models.
        if model == "openrouter/free":

            request_kwargs["extra_body"] = {
                "reasoning": {
                    "effort": "low"
                }
            }

        return request_kwargs

    # =========================================================
    # SEND PROMPT
    # =========================================================

    def send_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
        budget: Optional[float] = None,
    ) -> str:
        """
        Send an AI request with automatic model fallback.
        """

        if not prompt or not str(prompt).strip():
            raise AIServiceError(
                "AI prompt cannot be empty."
            )

        effective_max_tokens = (
            max_tokens
            if max_tokens is not None
            else self.max_output_tokens
        )

        effective_temperature = (
            temperature
            if temperature is not None
            else self.temperature
        )

        # Never allow invalid token values.
        try:
            effective_max_tokens = max(
                100,
                int(effective_max_tokens),
            )
        except (
            TypeError,
            ValueError,
        ):
            effective_max_tokens = 1200

        messages: List[Dict[str, str]] = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": str(system_prompt),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": str(prompt),
            }
        )

        models_to_try = list(
            dict.fromkeys(
                [
                    self.model,
                    *self.fallback_models,
                ]
            )
        )

        logger.info(
            "Sending AI request. models=%s "
            "max_tokens=%s json=%s",
            models_to_try,
            effective_max_tokens,
            json_mode,
        )

        last_error: Optional[Exception] = None

        started = time.monotonic()

        for index, model in enumerate(
            models_to_try,
            start=1,
        ):

            logger.info(
                "Attempting AI model %s/%s: %s",
                index,
                len(models_to_try),
                model,
            )

            request_kwargs = self._build_request(
                model=model,
                messages=messages,
                max_tokens=effective_max_tokens,
                temperature=effective_temperature,
                json_mode=json_mode,
            )

            # Hard time budget across all models, so a slow free model
            # can never make the whole analysis hang for minutes.
            if budget is not None:

                remaining = budget - (time.monotonic() - started)

                if remaining < 3:
                    logger.warning(
                        "AI time budget (%ss) used up before trying %s.",
                        budget,
                        model,
                    )
                    break

                request_kwargs["timeout"] = min(
                    remaining,
                    float(os.getenv("AI_TIMEOUT_SECONDS", "25")),
                )

            try:

                response = (
                    self.client
                    .chat
                    .completions
                    .create(
                        **request_kwargs
                    )
                )

                if not response:
                    raise AIServiceError(
                        "AI provider returned an empty response."
                    )

                if not response.choices:
                    raise AIServiceError(
                        "AI provider returned no choices."
                    )

                message = response.choices[0].message

                if message is None:
                    raise AIServiceError(
                        "AI provider returned an empty message."
                    )

                content = message.content

                if content is None:
                    raise AIServiceError(
                        "AI provider returned empty content."
                    )

                content = str(content).strip()

                if not content:
                    raise AIServiceError(
                        "AI provider returned blank content."
                    )

                logger.info(
                    "AI model request succeeded. model=%s",
                    model,
                )

                return content

            except Exception as exc:

                last_error = exc

                logger.warning(
                    "AI model failed. model=%s error=%s",
                    model,
                    exc,
                )

                if (
                    self._is_fallback_error(exc)
                    and index < len(models_to_try)
                ):

                    next_model = models_to_try[index]

                    logger.warning(
                        "Switching AI model. "
                        "failed_model=%s next_model=%s",
                        model,
                        next_model,
                    )

                    continue

                logger.error(
                    "AI request failed for model %s.",
                    model,
                )

                if index >= len(models_to_try):
                    break

        if last_error:

            raise AIServiceError(
                "AI request failed after trying "
                f"{len(models_to_try)} model(s): "
                f"{last_error}"
            ) from last_error

        raise AIServiceError(
            "AI request failed: unknown AI service error."
        )

    # =========================================================
    # SEND JSON PROMPT
    # =========================================================

    def send_json_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        budget: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Send a prompt and return parsed JSON.

        If an AI model returns malformed JSON, this method
        raises AIServiceError so the caller can use a safe
        deterministic fallback.
        """

        response = self.send_prompt(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=True,
        )

        return self._extract_json(
            response
        )

    # =========================================================
    # SEND JSON STRING PROMPT
    # =========================================================

    def send_json_string_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:

        return self.send_prompt(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=True,
        )


# =============================================================
# SINGLETON
# =============================================================

_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """
    Return the shared AIService instance.
    """

    global _ai_service

    if _ai_service is None:
        _ai_service = AIService()

    return _ai_service