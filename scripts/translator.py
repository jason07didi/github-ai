from __future__ import annotations

import os
import re
from typing import Iterable

_CJK = re.compile(r"[\u3400-\u9fff]")


def contains_chinese(text: str) -> bool:
    return bool(_CJK.search(text or ""))


class LocalTranslator:
    """Lazy-loaded, local English-to-Chinese translator.

    No paid API key is required. The Hugging Face model is downloaded once and
    then can be cached by GitHub Actions.
    """

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.disabled = os.getenv("DISABLE_TRANSLATION", "0") == "1"
        self._tokenizer = None
        self._model = None
        self._opencc = None

    def _load(self) -> None:
        if self.disabled or self._model is not None:
            return
        from opencc import OpenCC
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        self._model.eval()
        self._opencc = OpenCC("t2s")

    def translate_many(self, texts: Iterable[str], batch_size: int = 12) -> list[str]:
        items = [self._clean_text(t) for t in texts]
        if not items:
            return []
        if self.disabled:
            return items

        self._load()
        assert self._tokenizer is not None and self._model is not None

        results: list[str] = []
        for start in range(0, len(items), batch_size):
            batch = items[start : start + batch_size]
            translated_batch = [""] * len(batch)
            pending_indices: list[int] = []
            pending_texts: list[str] = []

            for i, text in enumerate(batch):
                if not text or contains_chinese(text):
                    translated_batch[i] = text
                else:
                    pending_indices.append(i)
                    pending_texts.append(text)

            if pending_texts:
                encoded = self._tokenizer(
                    pending_texts,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=220,
                )
                generated = self._model.generate(
                    **encoded,
                    max_new_tokens=220,
                    num_beams=3,
                )
                decoded = self._tokenizer.batch_decode(generated, skip_special_tokens=True)
                for idx, value in zip(pending_indices, decoded):
                    value = value.strip()
                    if self._opencc:
                        value = self._opencc.convert(value)
                    translated_batch[idx] = value or batch[idx]

            results.extend(translated_batch)
        return results

    @staticmethod
    def _clean_text(text: str) -> str:
        text = " ".join((text or "").split())
        return text[:900]
