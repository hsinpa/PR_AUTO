import re

import httpx


def parse_link_header(link_header: str):
    if not link_header:
        return {}

    links = {}
    # Split by commas and parse each link
    for link in link_header.split(','):
        # Extract URL and rel type
        url_match = re.search(r'<([^>]+)>', link)
        rel_match = re.search(r'rel="([^"]+)"', link)

        if url_match and rel_match:
            url = url_match.group(1)
            rel = rel_match.group(1)
            links[rel] = url

    return links

async def send_github_comment(comment_url: str, comment_content: str, token: str,
                              sha: str = None, file_path: str = None, line_number: int = None):

    payload: dict[str, str | int] = {"body": comment_content}

    if line_number is not None and file_path is not None and sha is not None:
        payload["line"] = line_number
        payload["path"] = file_path
        payload["commit_id"] = sha
        payload["side"] = 'RIGHT'

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(comment_url, json=payload, headers=headers)
        response_json = response.json()
        if 'body' not in response_json:
            return await send_github_comment(comment_url, comment_content, token)

        return response

async def fetch_github_content(url: str, token: str):

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        return {
            'data': response.json(),
            'link_header': response.headers.get('link'),
            'headers': response.headers
        }