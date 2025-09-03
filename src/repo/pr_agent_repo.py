from src.agent.file_crawler.file_crawler_tool import FileCrawlerTool
from src.agent.pull_request.pr_bot_agent import PRBotAgent
from src.agent.pull_request.summary_prompt import PR_SUMMARY_HUMAN_PROMPT, PR_SUMMARY_SYSTEM_PROMPT
from src.utility.langfuse_helper import get_langfuse_callback
from src.utility.llm_state import LLMAPIConfig
from src.utility.model_loader import ClassicILLMLoader
from langchain_core.output_parsers import StrOutputParser
from src.utility.module_prompt_factory import ModulePromptFactory



class PRAgentRepo:
    def __init__(self, session_id: str, api_config: LLMAPIConfig):
        self._api_config = api_config
        self._langfuse_handler = get_langfuse_callback()
        self._llm_loader = ClassicILLMLoader(api_config)

    async def run_pr_agent(self, file_crawler: FileCrawlerTool, comment_url: str, short_summary: str,
                           patch_content: str, c_instruction: str):
        pull_comment_url = comment_url.replace('/issues/', '/pulls/')

        agent = PRBotAgent(self._llm_loader, file_crawler, line_specific_comment_url=pull_comment_url, general_comment_url=comment_url,)
        agent_graph = agent.create_graph()

        feedback_content = await agent_graph.ainvoke({
            'pr_patch': patch_content,
            'custom_instruction': c_instruction,
            'short_summary': short_summary,
        },
        {'run_name': 'PR Issues Agent', "callbacks": self._langfuse_handler })

        return feedback_content['plans']

    async def run_summary_agent(self, patch_content: str):
        llm = self._llm_loader.get_llm_model()
        simple_chain = ModulePromptFactory(
            StrOutputParser(),
            model=llm,
            name='Summary',
            system_prompt_text=PR_SUMMARY_SYSTEM_PROMPT,
            human_prompt_text=PR_SUMMARY_HUMAN_PROMPT,
        ).create_chain()

        r = await (simple_chain.with_config({"run_name": "PR Summary Agent", "callbacks": self._langfuse_handler}).ainvoke({'pr_patch': patch_content}))

        r = f'''### Summary
{r}\
'''
        return r