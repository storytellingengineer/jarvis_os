"""OpenAI Responses API and audio integration."""

import json
from collections.abc import Callable
from typing import Any

from openai import OpenAI

from app.config import Settings


class OpenAIProvider:
    """Generate text and speech using OpenAI models."""

    def __init__(self, settings: Settings) -> None:
        if not settings.llm_api_key:
            raise ValueError(
                "LLM_API_KEY is not configured. Add it to your .env file."
            )

        self._client = OpenAI(api_key=settings.llm_api_key)
        self._model = settings.llm_model
        self._web_search_enabled = settings.web_search_enabled
        self._stt_model = settings.stt_model
        self._tts_model = settings.tts_model
        self._tts_voice = settings.tts_voice

    def generate(self, prompt: str) -> str:
        response = self._client.responses.create(
            model=self._model,
            input=prompt,
        )
        return response.output_text

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "recording.webm",
        content_type: str = "audio/webm",
    ) -> str:
        """Convert an uploaded audio recording into text."""
        result = self._client.audio.transcriptions.create(
            model=self._stt_model,
            file=(filename, audio_bytes, content_type),
        )
        return result.text

    def synthesize_speech(self, text: str) -> bytes:
        """Convert JARVIS text into an MP3 voice response."""
        if not text.strip():
            raise ValueError("Speech text must not be empty")
        result = self._client.audio.speech.create(
            model=self._tts_model,
            voice=self._tts_voice,
            input=text,
            response_format="mp3",
        )
        return result.content

    def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        executor: Callable[[str, dict[str, Any]], Any],
    ) -> str:
        """Generate a response and execute requested function tools."""
        request_tools = list(tools)
        if self._web_search_enabled:
            request_tools.append({"type": "web_search"})

        response = self._client.responses.create(
            model=self._model,
            input=prompt,
            tools=request_tools,
        )

        while True:
            function_calls = [
                item for item in response.output if item.type == "function_call"
            ]
            if not function_calls:
                return response.output_text

            tool_outputs = []
            for call in function_calls:
                arguments = json.loads(call.arguments)
                result = executor(call.name, arguments)
                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": str(result),
                    }
                )

            response = self._client.responses.create(
                model=self._model,
                previous_response_id=response.id,
                input=tool_outputs,
                tools=request_tools,
            )
