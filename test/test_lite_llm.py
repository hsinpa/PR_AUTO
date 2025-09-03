import os
import sys
from langfuse.langchain import CallbackHandler

from src.agent.pull_request.pr_bot_agent import PRBotAgent
from src.utility.model_loader import ClassicILLMLoader

langfuse_handler = CallbackHandler()

sys.path.insert(0, os.getcwd())

def test_with_langgraph():
    agent = PRBotAgent(ClassicILLMLoader())
    agent_graph = agent.create_graph()

    feedback_content = agent_graph.invoke({
        'pr_patch': '',
        'custom_instruction': '',
    },
        {'run_name': 'PR Agent', "callbacks": [langfuse_handler]})

if __name__ == "__main__":
    test_with_langgraph()
