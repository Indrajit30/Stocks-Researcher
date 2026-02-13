# backend/services/llm.py
from __future__ import annotations
import os
from typing import List
import openai

class LLMError(Exception):
    pass

class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("OPENAI_API_KEY not set")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def summarize(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
