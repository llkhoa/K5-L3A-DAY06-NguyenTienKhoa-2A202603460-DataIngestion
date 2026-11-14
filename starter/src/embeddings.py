
"""Real embedding provider using OpenRouter API.

Model:
    intfloat/multilingual-e5-large

API:
    https://openrouter.ai/api/v1/embeddings

Dimensions:
    1024

Features:
    - Real API embeddings, no mock vectors.
    - E5 query/document prefixes.
    - Batch embedding.
    - Vector dimension and numerical validation.
    - L2 normalization.
"""

import os
from typing import Protocol

import numpy as np
from openai import OpenAI
from dotenv import load_dotenv


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(
        self, texts: list[str]
    ) -> list[list[float]]:
        ...

    def embed_query(self, question: str) -> list[float]:
        ...


class MyEmbedder:
    """OpenRouter multilingual E5 embedding adapter."""

    DEFAULT_MODEL = "intfloat/multilingual-e5-large"
    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    EXPECTED_DIMENSIONS = 1024

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        api_key: str | None = None,
        batch_size: int = 32,
        timeout: float = 120.0,
    ) -> None:

        load_dotenv()

        if not model_name:
            raise ValueError("model_name cannot be empty.")

        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0.")

        api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is missing. "
                "Please configure it in your environment or .env file."
            )

        self.model_name = model_name
        self.dimensions = self.EXPECTED_DIMENSIONS
        self.batch_size = batch_size

        self.client = OpenAI(
            api_key=api_key,
            base_url=self.DEFAULT_BASE_URL,
            timeout=timeout,
            max_retries=3,
        )

        self.is_e5 = "e5" in model_name.lower()

        print("OpenRouter embedding client initialized.")
        print(f"Model: {self.model_name}")
        print(f"Expected dimensions: {self.dimensions}")
        print(f"Batch size: {self.batch_size}")

    def _prepare_document(self, text: str) -> str:
        """Prepare document text for E5 embedding."""

        if self.is_e5:
            return f"passage: {text}"

        return text

    def _prepare_query(self, question: str) -> str:
        """Prepare query text for E5 embedding."""

        if self.is_e5:
            return f"query: {question}"

        return question

    def _validate_vector(
        self,
        vector: list[float],
    ) -> list[float]:
        """Validate vector dimension and numerical values."""

        array = np.asarray(vector, dtype=np.float32)

        if array.ndim != 1:
            raise ValueError(
                f"Expected a 1D vector, got {array.shape}"
            )

        if len(array) != self.dimensions:
            raise ValueError(
                f"Expected {self.dimensions} dimensions, "
                f"received {len(array)}. "
                "Check whether the selected model has changed."
            )

        if not np.all(np.isfinite(array)):
            raise ValueError(
                "Embedding contains NaN or infinite values."
            )

        norm = np.linalg.norm(array)

        if norm == 0:
            raise ValueError("Embedding vector has zero norm.")

        # Normalize locally for consistent cosine similarity.
        array = array / norm

        return array.tolist()

    def _embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Send one batch to OpenRouter and preserve input order."""

        if not texts:
            return []

        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts,
            encoding_format="float",
        )

        if len(response.data) != len(texts):
            raise RuntimeError(
                f"Expected {len(texts)} embeddings, "
                f"received {len(response.data)}."
            )

        # Sort by API-provided input index.
        ordered_data = sorted(
            response.data,
            key=lambda item: item.index,
        )

        vectors = []

        for index, item in enumerate(ordered_data):
            if item.index != index:
                raise RuntimeError(
                    "Embedding response contains missing or duplicate indices."
                )

            vectors.append(
                self._validate_vector(item.embedding)
            )

        return vectors

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Embed document chunks in batches."""

        if not texts:
            return []

        if any(
            not isinstance(text, str) or not text.strip()
            for text in texts
        ):
            raise ValueError(
                "All document texts must be non-empty strings."
            )

        prepared_texts = [
            self._prepare_document(text)
            for text in texts
        ]

        all_vectors = []

        for start in range(0, len(prepared_texts), self.batch_size):
            batch = prepared_texts[
                start:start + self.batch_size
            ]

            vectors = self._embed_batch(batch)
            all_vectors.extend(vectors)

            print(
                f"Embedded {min(start + len(batch), len(texts))}"
                f"/{len(texts)} documents"
            )

        if len(all_vectors) != len(texts):
            raise RuntimeError(
                "Number of embeddings does not match input documents."
            )

        return all_vectors

    def embed_query(
        self,
        question: str,
    ) -> list[float]:
        """Embed a single search query."""

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Query cannot be empty.")

        prepared_question = self._prepare_query(question)

        vectors = self._embed_batch([prepared_question])

        return vectors[0]
