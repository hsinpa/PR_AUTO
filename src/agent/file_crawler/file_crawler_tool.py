from typing import Tuple
from src.github_tools.github_files import fetch_full_files, find_import_scripts_str, script_and_dependency_str
from src.model.pull_request_model import FileModel


class FileCrawlerTool:
    def __init__(self, commit_file_array: list[FileModel], content_url: str, sha: str, token: str):
        self.commit_file_array = commit_file_array
        self.file_table: dict[str, FileModel] = {}
        self.content_url = content_url
        self.sha = sha
        self.token = token

        for commit_file in self.commit_file_array:
            self.file_table[commit_file.filename] = commit_file

    def get_commit_files_dependencies_str(self):
        return self.get_files_dependencies_str([f.filename for f in self.commit_file_array])

    def get_files_dependencies_str(self, file_paths: list[str]):
        file_dependency_list = []

        for commit_file in file_paths:
            if commit_file in self.file_table:
                file_dependency_list.append(script_and_dependency_str(self.file_table[commit_file]))

        return '\n\n'.join(file_dependency_list)


    def get_files_str(self, file_paths: list[str]):
        file_dependency_list = []

        for commit_file in file_paths:
            if commit_file in self.file_table:
                file_dependency_list.append(
                    f'''File name: {self.file_table[commit_file].filename}
    File content: {self.file_table[commit_file].raw_content}'''
                )

        return '\n\n'.join(file_dependency_list)


    async def search_script_contents(self, commit_file_array: list[FileModel])-> Tuple[list[FileModel], str, str]:
        """Search the dependency for what is useful"""
        commit_file_array, full_concat_script = await fetch_full_files(commit_file_array, self.content_url, self.sha, self.token)
        return commit_file_array, full_concat_script, find_import_scripts_str(commit_file_array)

    async def fetch_llm_files_content(self, llm_files: list[dict]):
        format_files_list: list[str] = []

        for llm_file in llm_files:
            if llm_file['file_path'] in self.file_table:
                self.file_table[llm_file['file_path']].dependency_paths.extend(llm_file['dependency_paths'])
                format_files_list.extend(llm_file['dependency_paths'])

        format_files = [FileModel(filename=format_file) for format_file in format_files_list]
        dependent_file_array, _, _ = await self.search_script_contents(format_files)

        for dependent_file in dependent_file_array:
            if dependent_file.filename not in self.file_table:
                self.file_table[dependent_file.filename] = dependent_file