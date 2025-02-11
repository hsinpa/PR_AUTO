import os
import requests


def send_github_comment(comment_url: str, comment_content: str):
    pat = os.getenv('BOT_GH_PAT')

    if pat is None:
        return

    payload = {
        "body": comment_content,
    }

    # Set up the headers with the authentication token
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {pat}",
        "X-GitHub-Api-Version": "2022-11-28"
        }

    response = requests.post(comment_url, json=payload, headers=headers)


