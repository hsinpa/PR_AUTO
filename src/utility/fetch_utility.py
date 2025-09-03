import json
from pydantic import BaseModel, TypeAdapter
import httpx

from src.model.pull_request_model import FileModel


async def fetch_url(url: str, headers: dict):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.text

async def fetch_github_patch(pull_request_url: str, token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.patch",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:
        return await fetch_url(pull_request_url, headers)
    except Exception as e :
        print(f'fetch_github_patch: {pull_request_url}', e)
        return ''


async def fetch_github_file(content_url: str, file_path: str, sha: str, token: str) -> str:
    full_url = content_url.replace('{+path}', file_path)
    full_url += f'?ref={sha}'

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "Python-App/1.0"
    }

    try:
        return await fetch_url(full_url, headers)
    except Exception as e :
        print(f'fetch_github_file: {full_url}', e)
        return ''

async def fetch_github_files(content_url: str, token: str) -> list[FileModel]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:
        ta = TypeAdapter(list[FileModel])
        files = ta.validate_python(json.loads(await fetch_url(content_url, headers)))

        return files
    except Exception as e:
        print(f'fetch_github_file: {content_url}', e)
        return []