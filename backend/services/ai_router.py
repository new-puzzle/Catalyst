from typing import List, Optional
import httpx
import logging
from fastapi import HTTPException
from ..config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


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

        try:
            if provider == "gemini":
                return await self._call_gemini(messages)
            elif provider == "deepseek":
                return await self._call_deepseek(messages)
            elif provider == "claude":
                return await self._call_claude(messages)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in AI router: {e}")
            raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

    async def _call_gemini(self, messages: List[dict]) -> dict:
        """Call Google Gemini Flash API."""
        if not settings.gemini_api_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        try:
            async with httpx.AsyncClient() as client:
                # Convert messages to Gemini format
                contents = []
                for msg in messages:
                    if msg["role"] == "system":
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

                if response.status_code != 200:
                    logger.error(f"Gemini API returned {response.status_code}: {response.text[:500]}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"Gemini API error (status {response.status_code}). Please try again."
                    )

                data = response.json()

                if "error" in data:
                    error_msg = data['error'].get('message', 'Unknown error')
                    logger.error(f"Gemini error: {error_msg}")
                    raise HTTPException(status_code=502, detail=f"Gemini error: {error_msg}")

                if "candidates" in data and data["candidates"]:
                    try:
                        content = data["candidates"][0]["content"]["parts"][0]["text"]
                        tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
                        return {
                            "content": content,
                            "provider": "gemini",
                            "tokens_used": tokens,
                            "cost": (tokens / 1_000_000) * self.COSTS["gemini"],
                        }
                    except (KeyError, IndexError) as e:
                        logger.error(f"Failed to parse Gemini response: {e}, data: {data}")
                        raise HTTPException(status_code=502, detail="Invalid response structure from Gemini")

                logger.error(f"No candidates in Gemini response: {data}")
                raise HTTPException(status_code=502, detail="No response from Gemini")

        except httpx.TimeoutException:
            logger.error("Gemini API timeout")
            raise HTTPException(status_code=504, detail="Gemini API timeout. Please try again.")
        except httpx.RequestError as e:
            logger.error(f"Gemini network error: {e}")
            raise HTTPException(status_code=503, detail=f"Network error connecting to Gemini: {str(e)}")

    async def _call_deepseek(self, messages: List[dict]) -> dict:
        """Call DeepSeek API."""
        if not settings.deepseek_api_key:
            raise HTTPException(status_code=500, detail="DeepSeek API key not configured")

        try:
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

                if response.status_code != 200:
                    logger.error(f"DeepSeek API returned {response.status_code}: {response.text[:500]}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"DeepSeek API error (status {response.status_code}). Please try again."
                    )

                data = response.json()

                if "error" in data:
                    error_msg = data['error'].get('message', 'Unknown error')
                    logger.error(f"DeepSeek error: {error_msg}")
                    raise HTTPException(status_code=502, detail=f"DeepSeek error: {error_msg}")

                if "choices" in data and data["choices"]:
                    try:
                        content = data["choices"][0]["message"]["content"]
                        tokens = data.get("usage", {}).get("total_tokens", 0)
                        return {
                            "content": content,
                            "provider": "deepseek",
                            "tokens_used": tokens,
                            "cost": (tokens / 1_000_000) * self.COSTS["deepseek"],
                        }
                    except (KeyError, IndexError) as e:
                        logger.error(f"Failed to parse DeepSeek response: {e}, data: {data}")
                        raise HTTPException(status_code=502, detail="Invalid response structure from DeepSeek")

                logger.error(f"No choices in DeepSeek response: {data}")
                raise HTTPException(status_code=502, detail="No response from DeepSeek")

        except httpx.TimeoutException:
            logger.error("DeepSeek API timeout")
            raise HTTPException(status_code=504, detail="DeepSeek API timeout. Please try again.")
        except httpx.RequestError as e:
            logger.error(f"DeepSeek network error: {e}")
            raise HTTPException(status_code=503, detail=f"Network error connecting to DeepSeek: {str(e)}")

    async def _call_claude(self, messages: List[dict]) -> dict:
        """Call Anthropic Claude API."""
        if not settings.anthropic_api_key:
            raise HTTPException(status_code=500, detail="Anthropic API key not configured")

        try:
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

                if response.status_code != 200:
                    logger.error(f"Claude API returned {response.status_code}: {response.text[:500]}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"Claude API error (status {response.status_code}). Please try again."
                    )

                data = response.json()

                if "error" in data:
                    error_msg = data['error'].get('message', 'Unknown error')
                    logger.error(f"Claude error: {error_msg}")
                    raise HTTPException(status_code=502, detail=f"Claude error: {error_msg}")

                if "content" in data and data["content"]:
                    try:
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
                    except (KeyError, IndexError) as e:
                        logger.error(f"Failed to parse Claude response: {e}, data: {data}")
                        raise HTTPException(status_code=502, detail="Invalid response structure from Claude")

                logger.error(f"No content in Claude response: {data}")
                raise HTTPException(status_code=502, detail="No response from Claude")

        except httpx.TimeoutException:
            logger.error("Claude API timeout")
            raise HTTPException(status_code=504, detail="Claude API timeout. Please try again.")
        except httpx.RequestError as e:
            logger.error(f"Claude network error: {e}")
            raise HTTPException(status_code=503, detail=f"Network error connecting to Claude: {str(e)}")


ai_router = AIRouter()
