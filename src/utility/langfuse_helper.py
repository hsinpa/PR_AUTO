import os

from langfuse.callback import CallbackHandler
from typing import List

def get_langfuse_callback(session_id: str = None, tags: List[str] = []) -> list[CallbackHandler]:
    langfuse_secret = os.getenv('LANGFUSE_SECRET_KEY')
    langfuse_public = os.getenv('LANGFUSE_PUBLIC_KEY')
    langfuse_host = os.getenv('LANGFUSE_HOST')

    if langfuse_host is None or langfuse_public is None or langfuse_secret is None or langfuse_public is None:
        return []

    langfuse_handler = CallbackHandler(
        user_id='pr_chatbot',
        host=langfuse_host,
        public_key=langfuse_public,
        secret_key=langfuse_secret,
    )

    if session_id is not None:
        langfuse_handler.session_id = session_id

    if tags:
        langfuse_handler.tags = tags

    return [langfuse_handler]
