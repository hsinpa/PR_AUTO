import asyncio
from asyncio import Task

from langchain_core.output_parsers import StrOutputParser
from langgraph.constants import END
from langgraph.graph import StateGraph

from src.agent.file_crawler.file_crawler_prompt import FILE_CRAWLER_SYSTEM_PROMPT, FILE_CRAWLER_HUMAN_PROMPT
from src.agent.file_crawler.file_crawler_tool import FileCrawlerTool
from src.agent.pull_request.pr_agent_tool import get_custom_instruction, get_comment_content, split_git_patches, \
    git_patches_to_text
from src.agent.pull_request.pr_bot_state import ChatbotAgentState
from src.agent.pull_request.pr_draft_prompt import PR_DRAFT_SYSTEM_PROMPT, PR_DRAFT_HUMAN_PROMPT
from src.agent.pull_request.pr_plan_prompt import PLAN_SYSTEM_PROMPT, PLAN_HUMAN_PROMPT, CODE_REVIEW_RULE
from src.agent.pull_request.white_list_static import USEFUL_CODE_EXTS
from src.github_tools.github_comment import send_github_comment
from src.model.pull_request_model import PullRequestIssueModel
from src.utility.model_loader import ILLMLoader
from src.utility.module_prompt_factory import ModulePromptFactory
from src.utility.utility_func import parse_json, get_priority_markdown, clamp


class PRBotAgent:
    def __init__(self, llm_loader: ILLMLoader, file_crawler: FileCrawlerTool, general_comment_url: str,
                 line_specific_comment_url: str):
        self._llm_loader = llm_loader
        self._file_crawler = file_crawler
        self._general_comment_url = general_comment_url
        self._line_specific_comment_url = line_specific_comment_url
        self.pr_patch_sections = []


    async def _file_preparation(self, state: ChatbotAgentState):
        """ Get all the file dependencies path """
        commit_file_array, commit_file_concat_str, file_dependencies_str = await self._file_crawler.search_script_contents(self._file_crawler.commit_file_array)
        self._file_crawler.commit_file_array = commit_file_array
        self.pr_patch_sections = split_git_patches(state['pr_patch'], USEFUL_CODE_EXTS)

        return {'file_commit_concat_text': commit_file_concat_str,'file_dependency_paths_text': file_dependencies_str}

    async def _llm_file_dependency_path(self, state: ChatbotAgentState):
        """ Grab and fetch the script content from all dependencies """
        llm = self._llm_loader.get_llm_model()
        simple_chain = ModulePromptFactory(
            StrOutputParser(),
            model=llm,
            name='File crawler',
            system_prompt_text=FILE_CRAWLER_SYSTEM_PROMPT,
            human_prompt_text=FILE_CRAWLER_HUMAN_PROMPT,
        ).create_chain()

        r = await (simple_chain.with_config({"run_name": "File crawler"}).ainvoke({'file_dependency_paths_text': state['file_dependency_paths_text']}))
        dependencies_list: list[dict] = parse_json(r)

        await self._file_crawler.fetch_llm_files_content(dependencies_list)

        return {'file_lookup_table': self._file_crawler.file_table}

    async def _llm_pr_draft_plan(self, state: ChatbotAgentState):
        llm = self._llm_loader.get_llm_model()
        simple_chain = ModulePromptFactory(
            StrOutputParser(),
            model=llm,
            name='PR Drafts',
            system_prompt_text=PR_DRAFT_SYSTEM_PROMPT,
            human_prompt_text=PR_DRAFT_HUMAN_PROMPT,
        ).create_chain()

        r = await (simple_chain.with_config({"run_name": "PR Drafts"}).ainvoke({
            'pr_patch': git_patches_to_text(self.pr_patch_sections),
            'short_summary': state['short_summary'],
            'custom_instruction': get_custom_instruction(state['custom_instruction']),
            'committed_file_and_dependency': self._file_crawler.get_commit_files_dependencies_str(),
        }))

        drafts_list: list[dict] = parse_json(r)

        return {'drafts': drafts_list}

    async def _llm_pr_review_plans(self, state: ChatbotAgentState):
        draft_list = state['drafts']

        tasks: list[Task] = []
        async with asyncio.TaskGroup() as tg:
            for index, draft in enumerate(draft_list):
                line_number = -1 # Disable the line_number for now, llm can't distinguish the correct line_number

                # If LLM forget to provide one of the variable
                if 'pr_patch_index' not in draft or 'title' not in draft or 'priority' not in draft or \
                    'issue' not in draft or 'file_path' not in draft or 'dependency_paths' not in draft:
                    continue

                pr_patch_index = clamp(draft['pr_patch_index'], 0, len(self.pr_patch_sections))
                print('pr_patch_index', pr_patch_index)
                if pr_patch_index < 0 or pr_patch_index >= len(self.pr_patch_sections):
                    continue

                patch_content = self.pr_patch_sections[pr_patch_index]
                tasks.append(
                    tg.create_task(
                        self._llm_pr_review_plan(
                            index=index,
                            patch=patch_content,
                            title=draft['title'],
                            priority=draft.get('priority', 'low'),
                            line_number=line_number, # Must larger than 0
                            instruction=get_custom_instruction(state['custom_instruction']),
                            issue=draft['issue'],
                            file_path=draft['file_path'],
                            dependency_paths=draft.get('dependency_paths', []),
                        )
                    )
                )

        plans: list[PullRequestIssueModel] = []

        for t_index, task in enumerate(tasks):
            t_content = task.result()
            plans.append(t_content)

        return {'plans': plans}

    async def _llm_pr_review_plan(self, index: int, patch: str, title: str, priority: str, line_number,
                                  instruction: str, issue: str, file_path: str,  dependency_paths: list[str]) -> PullRequestIssueModel:
        llm = self._llm_loader.get_llm_model()

        filter_line_number = None if line_number < 0 else line_number

        simple_chain = ModulePromptFactory(
            StrOutputParser(),
            model=llm,
            name=f'PR Bot Review Index: {index}',
            partial_variables={
                'pr_patch': patch,
                'custom_instruction': instruction,
                'issue': issue,
                'file_script': self._file_crawler.get_files_str([file_path]),
                'dependency_script': self._file_crawler.get_files_str(dependency_paths),
                'title': title,
            },
            system_prompt_text=PLAN_SYSTEM_PROMPT,
            human_prompt_text=PLAN_HUMAN_PROMPT,
        ).create_chain()

        r = await (simple_chain.with_config({"run_name": f"PR Plan: {index}"}).ainvoke({}))

        # Send Github comment once ready
        await send_github_comment(self._general_comment_url if filter_line_number is None else self._line_specific_comment_url,
                            get_comment_content(title, priority, r),
                            self._file_crawler.token, sha=self._file_crawler.sha, file_path=file_path,
                            line_number=filter_line_number)

        return PullRequestIssueModel(
            pr_patch=patch,
            title=title,
            issue=issue,
            priority=priority,
            file_path=file_path,
            dependency_paths=dependency_paths,
            line_number=line_number,
            content=r
        )

    def create_graph(self):
        g_workflow = StateGraph(ChatbotAgentState)

        g_workflow.add_node('generate_plan_llm_node', self._llm_pr_review_plans)
        g_workflow.add_node('generate_draft_llm_node', self._llm_pr_draft_plan)

        g_workflow.add_node('file_preparation_node', self._file_preparation)
        g_workflow.add_node('file_dependency_path_node', self._llm_file_dependency_path)

        g_workflow.set_entry_point('file_preparation_node')
        g_workflow.add_edge('file_preparation_node', 'file_dependency_path_node')
        g_workflow.add_edge('file_dependency_path_node', 'generate_draft_llm_node')
        g_workflow.add_edge('generate_draft_llm_node', 'generate_plan_llm_node')

        g_workflow.add_edge('generate_plan_llm_node', END)

        g_compile = g_workflow.compile()
        return g_compile

