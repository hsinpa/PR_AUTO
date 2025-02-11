import sys
from dotenv import load_dotenv

from filter_pr_helper import filter_patch
from src.github_comment import send_github_comment
from src.pr_bot_agent import PRBotAgent
from src.utility.langfuse_helper import get_langfuse_callback
from src.utility.model_loader import ClassicILLMLoader


def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python my_script.py <patch_file>")
        sys.exit(1)

    patch_file = sys.argv[1]
    comment_url = sys.argv[2]

    try:
        with open(patch_file, 'r') as file:
            patch_lines = file.readlines()

            filtered_p = ''.join(filter_patch(patch_lines))

            agent = PRBotAgent(ClassicILLMLoader())
            agent_graph = agent.create_graph()

            feedback_content = agent_graph.invoke({
                'pr_patch': filtered_p
            },
            {'run_name': 'Lesson Summary v2', "callbacks": get_langfuse_callback()})

            send_github_comment(comment_url, feedback_content['plan'])

    except Exception as e:
        print(f"Error reading {patch_file}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
