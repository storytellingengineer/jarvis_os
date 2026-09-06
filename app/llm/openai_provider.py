"""OpenAI Responses API integration."""

from openai import OpenAI

from app.config import Settings


class OpenAIProvider:
    """Generate responses using an OpenAI model."""

    def __init__(self, settings: Settings) -> None:
        if not settings.llm_api_key:
            raise ValueError(
                "LLM_API_KEY is not configured. Add it to your .env file."
            )

        self._client = OpenAI(api_key=settings.llm_api_key)
        self._model = settings.llm_model

    def generate(self, prompt: str) -> str:
        response = self._client.responses.create(
            model=self._model,
            input=prompt,
        )
        return response.output_text
