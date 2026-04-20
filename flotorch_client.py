from __future__ import annotations

import os
import time
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
        self.max_retries = int(os.getenv("FLOTORCH_MAX_RETRIES", "3"))

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

        response: requests.Response | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )

                # Retry temporary upstream gateway issues before surfacing the failure.
                if response.status_code in {502, 503, 504} and attempt < self.max_retries:
                    time.sleep(min(2 ** (attempt - 1), 4))
                    continue

                response.raise_for_status()
                break
            except requests.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else "unknown"
                response_text = (exc.response.text or "").strip() if exc.response is not None else ""
                if status_code in {502, 503, 504} and attempt < self.max_retries:
                    time.sleep(min(2 ** (attempt - 1), 4))
                    continue
                details = f"FloTorch API error ({status_code}): {exc}"
                if response_text:
                    details += f"\nResponse body: {response_text[:500]}"
                raise RuntimeError(details) from exc
            except requests.RequestException as exc:
                if attempt < self.max_retries:
                    time.sleep(min(2 ** (attempt - 1), 4))
                    continue
                raise RuntimeError(f"FloTorch request failed: {exc}") from exc

        if response is None:
            raise RuntimeError("FloTorch request failed before receiving a response.")

        return self._parse_response(response.json())
