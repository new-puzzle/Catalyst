from typing import List, Optional
import httpx
from ..config import get_settings

settings = get_settings()


class AIRouter:
    """Routes requests to appropriate AI providers based on mode."""

    # Mode to provider mapping
    MODE_PROVIDERS = {
        "auto": "gemini",
        "architect": "deepseek",
        "simulator": "claude",
        "scribe": "claude",
    }

    # Cost per 1M tokens (input + output averaged)
    COSTS = {
        "gemini": 0.075,
        "deepseek": 0.14,
        "claude": 3.00,
    }

    async def route(
        self,
        messages: List[dict],
        mode: str = "auto",
        override_provider: Optional[str] = None,
    ) -> dict:
        """Route to appropriate AI and get response."""
        provider = override_provider or self.MODE_PROVIDERS.get(mode, "gemini")

        if provider == "gemini":
            return await self._call_gemini(messages)
        elif provider == "deepseek":
            return await self._call_deepseek(messages)
        elif provider == "claude":
            return await self._call_claude(messages)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _call_gemini(self, messages: List[dict]) -> dict:
        """Call Google Gemini Flash API."""
        if not settings.gemini_api_key:
            return self._mock_response("gemini", messages)

        async with httpx.AsyncClient() as client:
            # Convert messages to Gemini format
            contents = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})

            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.gemini_api_key}",
                json={"contents": contents},
                timeout=30.0,
            )
            data = response.json()

            if "candidates" in data:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                tokens = data.get("usageMetadata", {}).get("totalTokenCount", 100)
                return {
                    "content": content,
                    "provider": "gemini",
                    "tokens_used": tokens,
                    "cost": (tokens / 1_000_000) * self.COSTS["gemini"],
                }

        return self._mock_response("gemini", messages)

    async def _call_deepseek(self, messages: List[dict]) -> dict:
        """Call DeepSeek API."""
        if not settings.deepseek_api_key:
            return self._mock_response("deepseek", messages)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                },
                timeout=30.0,
            )
            data = response.json()

            if "choices" in data:
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 100)
                return {
                    "content": content,
                    "provider": "deepseek",
                    "tokens_used": tokens,
                    "cost": (tokens / 1_000_000) * self.COSTS["deepseek"],
                }

        return self._mock_response("deepseek", messages)

    async def _call_claude(self, messages: List[dict]) -> dict:
        """Call Anthropic Claude API."""
        if not settings.anthropic_api_key:
            return self._mock_response("claude", messages)

        async with httpx.AsyncClient() as client:
            # Convert to Claude format
            system = ""
            claude_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system = msg["content"]
                else:
                    claude_messages.append(msg)

            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 1024,
                    "system": system,
                    "messages": claude_messages,
                },
                timeout=30.0,
            )
            data = response.json()

            if "content" in data:
                content = data["content"][0]["text"]
                tokens = data.get("usage", {}).get("input_tokens", 0) + data.get(
                    "usage", {}
                ).get("output_tokens", 0)
                return {
                    "content": content,
                    "provider": "claude",
                    "tokens_used": tokens,
                    "cost": (tokens / 1_000_000) * self.COSTS["claude"],
                }

        return self._mock_response("claude", messages)

    def _mock_response(self, provider: str, messages: List[dict]) -> dict:
        """Return mock response when API keys not configured."""
        last_message = messages[-1]["content"] if messages else ""

        responses = {
            "gemini": f"[Gemini Flash - Demo Mode] I received your message about: {last_message[:50]}... I'm here to help with your daily journaling and quick thoughts.",
            "deepseek": f"[DeepSeek - Demo Mode] Let me help you structure and plan: {last_message[:50]}... I'll break this down into actionable steps.",
            "claude": f"[Claude - Demo Mode] I'll provide deep analysis for: {last_message[:50]}... Let me craft a thoughtful response.",
        }

        return {
            "content": responses.get(provider, "Response from AI"),
            "provider": provider,
            "tokens_used": 100,
            "cost": (100 / 1_000_000) * self.COSTS.get(provider, 0.1),
        }


ai_router = AIRouter()
