"""
MedCode AI Agent -- Multi-Provider LLM Client
=============================================
Enhanced LLM client with provider chain:
  DeepSeek V4 (primary) -> Groq (8-key rotation) -> Cerebras (9-key rotation)
  -> Together -> Gemini -> Mistral -> OpenRouter

Features:
  - call_llm: standard async LLM call with retry
  - call_llm_json: JSON-mode with 3x retry + repair logic
  - Provider auto-fallback on rate limits / errors
  - V19: PHI de-identification before LLM calls
"""

import json
import os
import random
import re
import time
from typing import Optional, Tuple

import requests

from core.config import (
    DEEPSEEK_API_KEY, DEEPSEEK_URL, DEEPSEEK_MODEL,
    GROQ_KEYS, GROQ_URL, GROQ_MODEL,
    CEREBRAS_KEYS, CEREBRAS_URL, CEREBRAS_MODEL,
    TOGETHER_KEY, TOGETHER_URL, TOGETHER_MODEL,
    GEMINI_KEY, GEMINI_URL, GEMINI_MODEL,
    MISTRAL_KEY, MISTRAL_URL, MISTRAL_MODEL,
    OPENROUTER_KEY, OPENROUTER_URL, OPENROUTER_MODEL,
    LLM_TEMPERATURE, LLM_MAX_TOKENS,
)


def _deidentify_for_llm(text: str) -> Tuple[str, dict]:
    """
    V19: De-identify PHI before sending to LLM.
    Returns (deidentified_text, token_mapping) for re-identification.
    """
    try:
        from security.llm_phi_firewall import get_llm_phi_firewall
        firewall = get_llm_phi_firewall()
        deidentified, result = firewall.sanitize_for_llm(text)
        return deidentified, {"tokens": [t.to_dict() for t in result.tokens]}
    except ImportError:
        return text, {}


class LLMClient:
    """
    Multi-provider LLM client with DeepSeek V4 as primary.
    Falls back through Groq (8 keys) -> Cerebras (9 keys) -> others.
    Tracks rate-limited providers and skips them for ~30s.
    """

    RATE_LIMIT_BACKOFF_SECONDS = 30

    def __init__(self):
        self._stats = {"calls": 0, "provider_used": None}
        self._rate_limited_until: dict[str, float] = {}
        self._log_providers()

    def _log_providers(self):
        active = []
        if DEEPSEEK_API_KEY:
            active.append("DeepSeek (primary)")
        if GROQ_KEYS:
            active.append(f"Groq ({len(GROQ_KEYS)} keys)")
        if CEREBRAS_KEYS:
            active.append(f"Cerebras ({len(CEREBRAS_KEYS)} keys)")
        if TOGETHER_KEY:
            active.append("Together")
        if GEMINI_KEY:
            active.append("Gemini")
        if MISTRAL_KEY:
            active.append("Mistral")
        if OPENROUTER_KEY:
            active.append("OpenRouter")
        print(f"  [LLM] Providers: {', '.join(active) if active else 'NONE!'}")

    def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = LLM_MAX_TOKENS,
        temperature: float = LLM_TEMPERATURE,
        deidentify_phi: bool = True,
    ) -> str:
        """
        Call LLM with system + user prompts. Tries providers in chain order.
        Returns response text or empty string on total failure.
        
        V19: De-identifies PHI before sending to LLM when deidentify_phi=True.
        """
        if deidentify_phi:
            user_prompt, _ = _deidentify_for_llm(user_prompt)
            system_prompt, _ = _deidentify_for_llm(system_prompt)

        messages = [{"role": "user", "content": user_prompt}]

        providers = self._build_provider_list()

        for name, func in providers:
            try:
                result = func(messages, system_prompt, max_tokens, temperature)
                if result and result != "rate_limited" and not result.startswith("Error:"):
                    self._stats["calls"] += 1
                    self._stats["provider_used"] = name
                    return result
                msg = "rate limited" if result == "rate_limited" else (result[:50] if result else "empty")
                print(f"  [LLM] {name} failed ({msg})")
            except Exception as e:
                print(f"  [LLM] {name} exception: {str(e)[:70]}")

        print("  [LLM] All providers exhausted.")
        return ""

    def call_llm_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = LLM_MAX_TOKENS,
        retries: int = 3,
    ) -> dict:
        """
        Call LLM and parse JSON response. Retries up to 3x on parse failure.
        Returns parsed dict, or {} on total failure.
        """
        error_hint = ""
        for attempt in range(retries):
            prompt = user_prompt + "\n\n" + error_hint if error_hint else user_prompt
            raw = self.call_llm(system_prompt, prompt, max_tokens=max_tokens)
            if not raw:
                break

            # Try to extract JSON
            data = self._try_parse_json(raw)
            if data is not None:
                return data

            error_hint = "Your previous response was not valid JSON. Return ONLY valid JSON."

        return {}

    def _is_rate_limited(self, name: str) -> bool:
        """Check if a provider is still in rate-limit backoff."""
        if name in self._rate_limited_until:
            if time.time() < self._rate_limited_until[name]:
                return True
            else:
                del self._rate_limited_until[name]
        return False

    def _mark_rate_limited(self, name: str):
        """Mark a provider as rate-limited for backoff period."""
        self._rate_limited_until[name] = time.time() + self.RATE_LIMIT_BACKOFF_SECONDS

    def _build_provider_list(self) -> list:
        """Build ordered list of (name, function) providers."""
        providers = []
        if DEEPSEEK_API_KEY and not self._is_rate_limited("DeepSeek"):
            providers.append(("DeepSeek", self._deepseek))
        if GROQ_KEYS and not self._is_rate_limited("Groq"):
            providers.append(("Groq", self._groq))
        if CEREBRAS_KEYS and not self._is_rate_limited("Cerebras"):
            providers.append(("Cerebras", self._cerebras))
        if TOGETHER_KEY and not self._is_rate_limited("Together"):
            providers.append(("Together", self._together))
        if GEMINI_KEY and not self._is_rate_limited("Gemini"):
            providers.append(("Gemini", self._gemini))
        if MISTRAL_KEY and not self._is_rate_limited("Mistral"):
            providers.append(("Mistral", self._mistral))
        if OPENROUTER_KEY and not self._is_rate_limited("OpenRouter"):
            providers.append(("OpenRouter", self._openrouter))
        return providers

    def _build_messages(self, messages: list, system: str) -> list:
        """Build message list with optional system prompt."""
        full = []
        if system:
            full.append({"role": "system", "content": system})
        full.extend(messages)
        return full

    def _post(
        self,
        url: str,
        headers: dict,
        payload: dict,
        name: str,
    ) -> str:
        """Send HTTP POST and return response text or error code."""
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            elif r.status_code == 429:
                return "rate_limited"
            elif r.status_code in (401, 403):
                return f"Error: {name} {r.status_code} -- auth"
            elif r.status_code == 402:
                return f"Error: {name} 402"
            else:
                return f"Error: {name} HTTP {r.status_code}"
        except requests.exceptions.Timeout:
            return f"Error: {name} timeout"
        except Exception as e:
            return f"Error: {name} -- {str(e)[:50]}"

    # -- Provider Implementations --------------------------------------

    def _deepseek(self, messages, system, max_tokens, temperature) -> str:
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": self._build_messages(messages, system),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        return self._post(DEEPSEEK_URL, headers, payload, "DeepSeek")

    def _groq(self, messages, system, max_tokens, temperature) -> str:
        keys = GROQ_KEYS.copy()
        random.shuffle(keys)
        for idx, key in enumerate(keys):
            payload = {
                "model": GROQ_MODEL,
                "messages": self._build_messages(messages, system),
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            result = self._post(GROQ_URL, headers, payload, f"Groq[key{idx+1}]")
            if result == "rate_limited":
                if idx == len(keys) - 1:  # All keys rate-limited
                    self._mark_rate_limited("Groq")
                continue
            if result and not result.startswith("Error:"):
                return result
        return "Error: All Groq keys exhausted"

    def _cerebras(self, messages, system, max_tokens, temperature) -> str:
        keys = CEREBRAS_KEYS.copy()
        random.shuffle(keys)
        for idx, key in enumerate(keys):
            payload = {
                "model": CEREBRAS_MODEL,
                "messages": self._build_messages(messages, system),
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            result = self._post(CEREBRAS_URL, headers, payload, f"Cerebras[key{idx+1}]")
            if result == "rate_limited":
                if idx == len(keys) - 1:  # All keys rate-limited
                    self._mark_rate_limited("Cerebras")
                continue
            if result and not result.startswith("Error:"):
                return result
        return "Error: All Cerebras keys exhausted"

    def _together(self, messages, system, max_tokens, temperature) -> str:
        payload = {
            "model": TOGETHER_MODEL,
            "messages": self._build_messages(messages, system),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {TOGETHER_KEY}",
            "Content-Type": "application/json",
        }
        return self._post(TOGETHER_URL, headers, payload, "Together")

    def _gemini(self, messages, system, max_tokens, temperature) -> str:
        url = f"{GEMINI_URL}?key={GEMINI_KEY}"
        payload = {
            "model": GEMINI_MODEL,
            "messages": self._build_messages(messages, system),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {"Content-Type": "application/json"}
        return self._post(url, headers, payload, "Gemini")

    def _mistral(self, messages, system, max_tokens, temperature) -> str:
        payload = {
            "model": MISTRAL_MODEL,
            "messages": self._build_messages(messages, system),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {MISTRAL_KEY}",
            "Content-Type": "application/json",
        }
        return self._post(MISTRAL_URL, headers, payload, "Mistral")

    def _openrouter(self, messages, system, max_tokens, temperature) -> str:
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": self._build_messages(messages, system),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        }
        return self._post(OPENROUTER_URL, headers, payload, "OpenRouter")

    # -- JSON Parsing Helpers ------------------------------------------

    def _try_parse_json(self, raw: str) -> Optional[dict]:
        """Attempt to parse JSON from LLM response, trying multiple cleanup strategies."""
        cleaned = raw.strip()

        # Strip markdown code blocks
        if "```" in cleaned:
            for part in cleaned.split("```"):
                stripped = part.replace("json", "").replace("JSON", "").strip()
                if stripped.startswith("{") or stripped.startswith("["):
                    cleaned = stripped
                    break

        # Direct parse
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                return {"results": data}
            return None
        except json.JSONDecodeError:
            pass

        # Clean trailing commas
        cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)

        # Try strict=False
        try:
            data = json.loads(cleaned, strict=False)
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                return {"results": data}
            return None
        except (json.JSONDecodeError, ValueError):
            pass

        # Handle "Extra data" with raw_decode
        try:
            decoder = json.JSONDecoder()
            data, idx = decoder.raw_decode(cleaned)
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                return {"results": data}
            return None
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

        return None

    def get_stats(self) -> dict:
        return self._stats.copy()
