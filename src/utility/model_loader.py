import os
from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel, FakeListChatModel
from langchain_openai import ChatOpenAI

GPT4o_mini = 'gpt-4o-mini'
GPT4o = 'gpt-4o'


class ILLMLoader(ABC):
    @abstractmethod
    def get_llm_model(self, model_name: str) -> BaseChatModel:
        """Must return a string based on integer x."""
        pass

class ClassicILLMLoader(ILLMLoader):
    def get_llm_model(self, model_name: str, **kwargs) -> BaseChatModel:
        table = {
            GPT4o_mini: self.openai_model,
            GPT4o: self.openai_model,
        }

        if model_name in table:
            return table[model_name](**kwargs)
        else:
            return self.openai_model(**kwargs)

    @staticmethod
    def openai_model(deployment_name: str = GPT4o_mini, **kwargs):
        cfg = {
            "model_name": deployment_name,
            "openai_api_key": os.getenv('OPENAI_API_KEY'),
        }
        return ChatOpenAI(**{**cfg, **kwargs})

class MockLLMLoader(ILLMLoader):
    def __init__(self, fake_response: list[str]):
        self._fake_response = fake_response

    def get_llm_model(self, model_name: str, **kwargs) -> BaseChatModel:
        return FakeListChatModel(responses=self._fake_response)
