import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

class LLMAPIConfig(BaseModel):
    model: str
    provider: str
    api_key: str
    api_base: Optional[str] = Field(default=None)
    api_version: Optional[str] = Field(default=None)

    @staticmethod
    def get_config():
        return LLMAPIConfig(
            model = os.getenv('LLM_MODEL'),
            provider=os.getenv('LLM_PROVIDER'),
            api_key = os.getenv('LLM_API_KEY'),
            api_base = os.getenv('LLM_API_BASE'),
            api_version = os.getenv('LLM_API_VERSION'),
        )

