from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


_ENV_PATH = Path(__file__).resolve().parent / ".env"
if not _ENV_PATH.exists():
    _ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(dotenv_path=_ENV_PATH)


class FloTorchClient:
    def __init__(self) -> None:
        self.api_url = os.getenv("FLOTORCH_API_URL")
        self.api_key = os.getenv("FLOTORCH_API_KEY")
        self.model = os.getenv("FLOTORCH_MODEL", "claude")
        self.index_id = os.getenv("FLOTORCH_INDEX_ID")
        self.timeout = int(os.getenv("FLOTORCH_TIMEOUT", "60"))

    def _build_payload(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self.index_id:
            payload["index_id"] = self.index_id
        return payload

    @staticmethod
    def _parse_response(data: Any) -> str:
        if isinstance(data, dict):
            if isinstance(data.get("output_text"), str):
                return data["output_text"]
            choices = data.get("choices")
            if isinstance(choices, list) and choices:
                message = choices[0].get("message", {})
                content = message.get("content")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    text_parts = [
                        item.get("text", "")
                        for item in content
                        if isinstance(item, dict) and isinstance(item.get("text"), str)
                    ]
                    if text_parts:
                        return "\n".join(text_parts).strip()
        raise RuntimeError(f"Unexpected FloTorch response shape: {data}")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_url or not self.api_key:
            raise EnvironmentError(
                "FLOTORCH_API_URL and FLOTORCH_API_KEY must be set in the project .env file."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = self._build_payload(system_prompt=system_prompt, user_prompt=user_prompt)

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(f"FloTorch API error: {exc}") from exc
        except requests.RequestException as exc:
            raise RuntimeError(f"FloTorch request failed: {exc}") from exc

        return self._parse_response(response.json())
