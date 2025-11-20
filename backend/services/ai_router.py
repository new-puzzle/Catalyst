from typing import List, Optional
import httpx
from fastapi import HTTPException
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
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        async with httpx.AsyncClient() as client:
            # Convert messages to Gemini format
            contents = []
            for msg in messages:
                if msg["role"] == "system":
                    # Gemini handles system prompts differently - prepend to first user message
                    continue
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})

            # Get system prompt if exists
            system_instruction = None
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                    break

            request_body = {"contents": contents}
            if system_instruction:
                request_body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.gemini_api_key}",
                json=request_body,
                timeout=60.0,
            )
            data = response.json()

            if "error" in data:
                raise HTTPException(status_code=500, detail=f"Gemini error: {data['error'].get('message', 'Unknown error')}")

            if "candidates" in data:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
                return {
                    "content": content,
                    "provider": "gemini",
                    "tokens_used": tokens,
                    "cost": (tokens / 1_000_000) * self.COSTS["gemini"],
                }

            raise HTTPException(status_code=500, detail="Invalid response from Gemini")

    async def _call_deepseek(self, messages: List[dict]) -> dict:
        """Call DeepSeek API."""
        if not settings.deepseek_api_key:
            raise HTTPException(status_code=500, detail="DeepSeek API key not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                },
                timeout=60.0,
            )
            data = response.json()

            if "error" in data:
                raise HTTPException(status_code=500, detail=f"DeepSeek error: {data['error'].get('message', 'Unknown error')}")

            if "choices" in data:
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                return {
                    "content": content,
                    "provider": "deepseek",
                    "tokens_used": tokens,
                    "cost": (tokens / 1_000_000) * self.COSTS["deepseek"],
                }

            raise HTTPException(status_code=500, detail="Invalid response from DeepSeek")

    async def _call_claude(self, messages: List[dict]) -> dict:
        """Call Anthropic Claude API."""
        if not settings.anthropic_api_key:
            raise HTTPException(status_code=500, detail="Anthropic API key not configured")

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
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1024,
                    "system": system,
                    "messages": claude_messages,
                },
                timeout=60.0,
            )
            data = response.json()

            if "error" in data:
                raise HTTPException(status_code=500, detail=f"Claude error: {data['error'].get('message', 'Unknown error')}")

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

            raise HTTPException(status_code=500, detail="Invalid response from Claude")


ai_router = AIRouter()
