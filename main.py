import asyncio
import json
import os
import sys
import uuid

from dotenv import load_dotenv

from src.agent.file_crawler.file_crawler_tool import FileCrawlerTool
from src.agent.pull_request.pr_agent_tool import get_comment_content, split_git_patches, git_patches_to_text
from src.agent.pull_request.white_list_static import USEFUL_CODE_EXTS
from src.github_tools.github_comment import send_github_comment, fetch_github_content, parse_link_header
from src.model.pull_request_model import PullRequestIssueModel
from src.repo.pr_agent_repo import PRAgentRepo
from src.utility.fetch_utility import fetch_github_file, fetch_github_patch, fetch_github_files
from src.utility.llm_state import LLMAPIConfig
from src.utility.static_variable import CUSTOM_INSTRUCTION_FILE
from src.utility.utility_func import timer


async def process_review(session_id: str, token: str, sha: str, comment_url: str,
                         content_url: str, self_repo_url: str, pull_request_url: str):
    api_config = LLMAPIConfig.get_config()
    pr_repo = PRAgentRepo(session_id, api_config)

    file_repo_url = self_repo_url+'/files'
    with timer('Fetch repo files'):
        async with asyncio.TaskGroup() as tg:
            patch_content_task = tg.create_task(
                fetch_github_patch(pull_request_url=pull_request_url, token=token)
            )

            # Get the custom instruction
            c_instruction_task = tg.create_task(
                fetch_github_file(content_url=content_url, file_path=CUSTOM_INSTRUCTION_FILE,
                                  sha=sha, token=token)
            )

            # Fetch a commit file list
            commit_files_task = tg.create_task(
                fetch_github_files(file_repo_url, token=token)
            )

    patch_content = patch_content_task.result()
    c_instruction = c_instruction_task.result()
    commit_file_array = commit_files_task.result()

    filter_pr_patch_sections = split_git_patches(patch_content, USEFUL_CODE_EXTS)
    filter_pr_patch_text = git_patches_to_text(filter_pr_patch_sections)

    file_crawler = FileCrawlerTool(commit_file_array, content_url=content_url, sha=sha, token=token)
    with timer('PR summary'):
        summary = await pr_repo.run_summary_agent(patch_content=filter_pr_patch_text)

    await send_github_comment(comment_url, summary, token)

    # Issue comment agent
    with timer('Issue planning'):
        feedback_contents: list[PullRequestIssueModel] = await pr_repo.run_pr_agent(patch_content=patch_content,
                                                       comment_url=comment_url,
                                                       c_instruction=c_instruction,
                                                       file_crawler=file_crawler,
                                                       short_summary=summary, )


async def process_comment(session_id: str, token: str, github_event_json: dict):
    if  'pull_request' not in github_event_json['issue']:
        return

    comment_url = github_event_json['issue']['comments_url']
    repo_url = github_event_json['issue']['pull_request']['url']

    with timer('Fetch comments'):
        page_comment_contents = await fetch_github_content(comment_url+"?per_page=1", token)
        page_link_headers = parse_link_header(page_comment_contents['link_header'])
        last_comment_url = page_link_headers.get('last')
        last_comment = (await fetch_github_content(last_comment_url, token))['data'][-1]['body']

        repo_contents = (await fetch_github_content(repo_url, token))['data']

    if last_comment == '/comment':
        await process_review(session_id=session_id, token=token,
                             sha=repo_contents['head']['sha'],
                             comment_url=repo_contents['comments_url'],
                             content_url=repo_contents['head']['repo']['contents_url'],
                             self_repo_url=repo_contents['_links']['self']['href'],
                             pull_request_url=repo_contents['url'])

async def main(github_event_json: dict):
    load_dotenv()
    session_id = str(uuid.uuid4())
    token = os.getenv('BOT_GH_TOKEN')

    event_name = os.getenv('EVENT_NAME')

    if event_name == 'issue_comment':
        await process_comment(session_id, token, github_event_json)
    else:
        sha = github_event_json['pull_request']['head']['sha']
        comment_url = github_event_json['pull_request']['comments_url']
        content_url = github_event_json['repository']['contents_url']
        self_repo_url = github_event_json['pull_request']['_links']['self']['href']
        pull_request_url = github_event_json['pull_request']['url']
        await process_review(session_id=session_id, token=token, sha=sha, comment_url=comment_url,
                             content_url=content_url, self_repo_url=self_repo_url, pull_request_url=pull_request_url)

if __name__ == "__main__":
    asyncio.run(main( json.loads(sys.argv[1]) ))
