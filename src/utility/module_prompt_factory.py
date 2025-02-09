from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import BaseOutputParser
from langchain.schema.messages import SystemMessage
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langfuse.callback import CallbackHandler


class ModulePromptFactory:
    """A factory only accept and run one prompt, nothing more"""

    def __init__(
        self,
        output_parser: BaseOutputParser,
        model: BaseChatModel,
        human_prompt_text: str,
        system_prompt_text: str = None,
        input_variables: list[str] = None,
        partial_variables: dict = None,
        temperature: float = 0.75,
        json_response: bool = False,
        name: str = None,
        langfuse_callback: CallbackHandler = None,
    ) -> None:
        if partial_variables is None:
            partial_variables = {}
        if input_variables is None:
            input_variables = []
        if system_prompt_text is None:
            system_prompt_text = "You are a helpful assistant."

        kwargs = {'temperature': temperature}
        if json_response is True:
            kwargs['model_kwargs'] = {"response_format": {"type": "json_object"}}

        self.human_prompt_text = human_prompt_text
        self.system_prompt_text = system_prompt_text

        self.output_parser = output_parser
        self.partial_variables = partial_variables
        self.input_variables = input_variables
        self.model = model.bind(stop=['<|eot_id|>'])
        self.name = name
        self.langfuse_callback = langfuse_callback

    def __create_prompt(self):
        messages = [
            SystemMessage(content=self.system_prompt_text),
            HumanMessagePromptTemplate.from_template(self.human_prompt_text),
        ]

        template = ChatPromptTemplate(
            messages=messages, input_variables=self.input_variables, partial_variables=self.partial_variables
        )

        return template

    def create_chain(self):

        if self.name is not None:
            self.model = self.model.with_config({"run_name": self.name})

        prompt = self.__create_prompt()
        chain = prompt | self.model | self.output_parser

        if self.langfuse_callback is not None:
            chain = chain.with_config({"callbacks": [self.langfuse_callback]})

        return chain
