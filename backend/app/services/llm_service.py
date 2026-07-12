import os
import json
import logging
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    _client = None

    @classmethod
    def get_client(cls) -> AsyncOpenAI:
        if cls._client is None:
            api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY not found. LLM service will fail if called.")
                raise ValueError("OPENAI_API_KEY not found")
            cls._client = AsyncOpenAI(api_key=api_key)
        return cls._client

    @classmethod
    async def generate_completion(
        cls, 
        system_prompt: str, 
        user_prompt: str, 
        model: str = "gpt-4o", 
        temperature: float = 0.7
    ) -> str:
        """
        Generates a standard text completion.
        """
        client = cls.get_client()
        try:
            response = await client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            raise e

    @classmethod
    async def generate_json(
        cls, 
        system_prompt: str, 
        user_prompt: str, 
        model: str = "gpt-4o", 
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generates a JSON response. The system_prompt MUST instruct the model to return JSON.
        """
        client = cls.get_client()
        try:
            response = await client.chat.completions.create(
                model=model,
                temperature=temperature,
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"LLM JSON extraction error: {e}")
            raise e

    @classmethod
    async def generate_chat(
        cls,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7
    ) -> str:
        """
        For multi-turn conversation. Messages should be standard OpenAI format:
        [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        """
        client = cls.get_client()
        try:
            response = await client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise e
