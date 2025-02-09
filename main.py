import sys
from dotenv import load_dotenv

from filter_pr_helper import filter_patch
from src.pr_bot_agent import PRBotAgent
from src.utility.langfuse_helper import get_langfuse_callback
from src.utility.model_loader import ClassicILLMLoader


def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python my_script.py <patch_file>")
        sys.exit(1)

    patch_file = sys.argv[1]

    try:
        with open(patch_file, 'r') as file:
            patch_lines = file.readlines()

            filtered_p = ''.join(filter_patch(patch_lines))

            agent = PRBotAgent(ClassicILLMLoader())
            agent_graph = agent.create_graph()

            agent_graph.ainvoke({
                'pr_patch': filtered_p
            },
            {'run_name': 'Lesson Summary v2', "callbacks": get_langfuse_callback()},
                                )
    except Exception as e:
        print(f"Error reading {patch_file}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
