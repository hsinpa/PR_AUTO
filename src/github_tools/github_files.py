import asyncio
import re

from src.model.pull_request_model import FileModel
from src.utility.fetch_utility import fetch_github_file

REGEX_FIND_IMPORT_SCRIPT = r'^([\s]*(?:import|from|#include|using|use|require|extern\s+crate)[\s\(\'\"]*.*?)[\s\)\'\";\}]*$'
regex_find_imports_cache = re.compile(REGEX_FIND_IMPORT_SCRIPT, re.MULTILINE)

async def fetch_full_files(commit_file_array: list[FileModel], content_url: str, sha: str, token: str):
    tasks = []

    unique_files = list({file.filename: file for file in commit_file_array}.values())
    print(f'unique_files length: {len(unique_files)}')

    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(fetch_github_file(content_url, file.filename, sha, token))
            for file in unique_files
        ]

    results = [task.result() for task in tasks]
    file_result = []

    files_concat_full_str = ''
    for file_model, raw_file in zip(unique_files, results):
        if raw_file == '':
            continue

        files_concat_full_str += (f'# region file {file_model.filename}:\n'
                                  f'{raw_file}\n'
                                  f'# endregion file {file_model.filename}\n\n')
        file_model.raw_content = raw_file
        file_result.append(file_model)

    return file_result, files_concat_full_str


def find_import_scripts_str(commit_file_array: list[FileModel]):
    all_dependencies_array = []
    unique_files = list({file.filename: file for file in commit_file_array}.values())

    for commit_file in unique_files:

        all_groups = regex_find_imports_cache.findall(commit_file.raw_content)

        script_and_dependency_str(commit_file)
        all_groups = [group.strip() for group in all_groups]
        dependencies = '\n'.join(all_groups)

        result = (f'From file path: {commit_file.filename}\n'
                  f'{dependencies}')

        if len(all_groups) > 0:
            all_dependencies_array.append(result)

    return '\n\n'.join(all_dependencies_array)


def script_and_dependency_str(file_model: FileModel):
    all_groups = [group.strip() for group in file_model.dependency_paths]
    dependencies = '\n'.join(all_groups)

    result = f'Main file path: {file_model.filename}\n'

    if len(all_groups) > 0:
        result +=  f'Dependencies: {dependencies}'

    return result