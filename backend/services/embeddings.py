# backend/services/embeddings.py
from __future__ import annotations
import os
from typing import List
import openai

class EmbeddingError(Exception):
    pass

class EmbeddingsClient:
    def __init__(self, model: str = "text-embedding-3-small"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EmbeddingError("OPENAI_API_KEY not set")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        resp = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        # Ensure order preserved
        return [d.embedding for d in resp.data]
