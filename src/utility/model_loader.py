import os
from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel, FakeListChatModel

from src.utility.llm_state import LLMAPIConfig

GPT4o_mini = 'gpt-4o-mini'
GPT4o = 'gpt-4o'
GPT41 = 'gpt-4.1'

class ILLMLoader(ABC):
    @abstractmethod
    def get_llm_model(self, provider: str=None, model_name: str=None) -> BaseChatModel:
        """Must return a string based on integer x."""
        pass

class ClassicILLMLoader(ILLMLoader):
    def __init__(self, default_api_config: LLMAPIConfig):
        self._default_api_config = default_api_config

    def get_llm_model(self, provider: str=None, model_name: str=None, **kwargs) -> BaseChatModel:
        if provider is None:
            provider = self._default_api_config.provider

        if model_name is None:
            model_name = self._default_api_config.model

        provider_table = {
            'openai': self.openai_model,
            'anthropic': self.anthropic_model,
            'azure': self.azure_model,
            'google_genai': self.google_genai_model,
        }

        if provider in provider_table:
            return provider_table[provider](deployment_name=model_name, **kwargs)

        raise RuntimeError(f"No such provider: '{provider}' and model: '{model_name}'")

    @staticmethod
    def openai_model(deployment_name: str, api_key=str, **kwargs):
        from langchain_openai import ChatOpenAI

        cfg = {
            "model_name": deployment_name,
            "openai_api_key": os.getenv('LLM_API_KEY'),
        }
        return ChatOpenAI(**{**cfg, **kwargs})

    @staticmethod
    def anthropic_model(deployment_name: str, **kwargs):
        from langchain_anthropic import ChatAnthropic

        cfg = {
            "model": deployment_name,
            "anthropic_api_key": os.getenv('LLM_API_KEY'),
        }
        return ChatAnthropic(**{**cfg, **kwargs})

    @staticmethod
    def azure_model(deployment_name: str, **kwargs):
        from langchain_openai import AzureChatOpenAI

        cfg = {
            "azure_deployment": deployment_name,
            "api_key": os.getenv('LLM_API_KEY'),
            "azure_endpoint": os.getenv('LLM_API_BASE'),
            "api_version": os.getenv('LLM_API_VERSION'),
        }
        return AzureChatOpenAI(**{**cfg, **kwargs})

    @staticmethod
    def google_genai_model(deployment_name: str, **kwargs):
        from langchain_google_genai import ChatGoogleGenerativeAI

        cfg = {
            "model": deployment_name,
            "google_api_key": os.getenv('LLM_API_KEY'),
        }
        return ChatGoogleGenerativeAI(**{**cfg, **kwargs})

class MockLLMLoader(ILLMLoader):
    def __init__(self, fake_response: list[str]):
        self._fake_response = fake_response

    def get_llm_model(self, provider: str=None, model_name: str=None, **kwargs) -> BaseChatModel:
        return FakeListChatModel(responses=self._fake_response)
