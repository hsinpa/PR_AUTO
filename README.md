# PR_AUTO

## Table of content
[Installation](#installation)  
[Supported LLM](#supported-llm)  
[Custom instruction](#custom-instruction)  
[How to prepare repository summary](#how-to-prepare-repository-summary)  

## Installation
### First step
Copy and paste the yaml file to `.github/workflows/pr_review_bot.yaml`
<details>
<summary>Yaml file in detail</summary>

``` yaml
name: AUTO PR Review
on:
  pull_request:
    types:
      - opened
      - reopened
  issue_comment:
    types:
      - created

jobs:
  auto-bot-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Checkout PR repository
        uses: actions/checkout@v4

      - name: Checkout private repository
        uses: actions/checkout@v4
        with:
          repository: SSS-Core-AI/pull-request-review-bot
          path: pull-request-review-bot
          ref: main

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv with caching
        uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
          cache-dependency-glob: |
            pull-request-review-bot/pyproject.toml
            pull-request-review-bot/uv.lock

      - name: Debug Environment
        working-directory: pull-request-review-bot
        run: |
          echo "=== GitHub Context ==="
          echo "Event name: '${{ github.event_name }}'"
          echo "Event action: '${{ github.event.action }}'"

      - name: Create .env file with multiple variables
        working-directory: pull-request-review-bot
        run: |
          cat << EOF > .env
          LLM_MODEL=gemini-2.5-flash-lite
          LLM_PROVIDER=google_genai
          LLM_API_KEY=${{secrets.LLM_API_KEY}}
          LANGFUSE_SECRET_KEY=${{secrets.LANGFUSE_SECRET_KEY}}
          LANGFUSE_PUBLIC_KEY=${{secrets.LANGFUSE_PUBLIC_KEY}}
          LANGFUSE_HOST=${{secrets.LANGFUSE_HOST}}
          BOT_GH_TOKEN=${{secrets.GITHUB_TOKEN}}
          EVENT_NAME=${{github.event_name}}
          $([ -n "${{secrets.LLM_API_BASE}}" ] && echo "LLM_API_BASE=${{secrets.LLM_API_BASE}}")
          $([ -n "${{secrets.LLM_API_VERSION}}" ] && echo "LLM_API_VERSION=${{secrets.LLM_API_VERSION}}")
          EOF

      - name: Install packages
        working-directory: pull-request-review-bot
        run: uv sync

      - name: Execute
        working-directory: pull-request-review-bot
        env:
          GITHUB_EVENT_JSON: ${{ toJSON(github.event) }}
        run: |
          uv run python -m main "$GITHUB_EVENT_JSON"
```
</details>

| Key | Existence | Description |
| ------------- | ------------- | ------------- |
| LLM_MODEL | required | Name of model  |
| LLM_PROVIDER | required | Name of llm provider  |
| LLM_API_KEY | required | Your api key  |
| LANGFUSE_SECRET_KEY | optional  | Optional lanfuse parameter  |
| LANGFUSE_PUBLIC_KEY | optional | Optional lanfuse parameter  |
| LANGFUSE_HOST | optional | Optional lanfuse parameter  |
| LLM_API_BASE | required => azure provider  | Ignore, if not using azure |
| LLM_API_VERSION | required => azure provider  | Ignore, if not using azure  |

### Secondary step
Add keys to repository secrets <br>
Repo settings => secrets and variables / actions => New repository secret
![image](https://github.com/user-attachments/assets/599f0742-5504-488c-9ebf-e47ffab39a70)


## Supported LLM
| Provider  | Models |
| ------------- | ------------- |
| openai  | [Table link](https://platform.openai.com/docs/models)  |
| azure  | [Table link](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/models?tabs=global-standard%2Cstandard-chat-completions)  |
| google_genai  | [Table link](https://ai.google.dev/gemini-api/docs/models)  |
| anthropic  | [Table link](https://docs.anthropic.com/en/docs/about-claude/models/overview)  |

For Azure, manually align the deploy model name to what is in the documentation

## Custom instruction
Create a file under `pr_agent_config/custom_instruction.txt`

<details>
<summary>Intstruction sample (Python as example)</summary>

``` txt
pr_agent_config/custom_instruction.txt

## Python Style and Formatting

PEP 8 compliance and specific style violations to look for
Import organization and formatting (PEP 328)
Naming conventions for variables, functions, classes, modules, and constants
Comment and docstring formatting (PEP 257)


## For each section, provide:

Good examples showing the Pythonic way
Bad examples showing common anti-patterns
Checklist items for reviewers
```
</details>



## How to prepare repository summary
1. **Checkout the files-to-prompt tool**</br>
Install this package https://github.com/simonw/files-to-prompt

2. **Generate the concatenated script file**</br>
For example
```bash
cd /path/to/your/project
files-to-prompt .\controllers\ .\models\ .\utils\ .\tests\ app.py main.py -e py -o output.txt
```

* `-e py` – include only `.py` files
* `-o output.txt` – write output to `output.txt`

3. **Analyze with your LLM**</br>
   Upload `output.txt` to ChatGPT (or another LLM) with:

   ```text
   System: You are an expert software engineer and technical writer.

   User: I’m giving you a large concatenated script file.
   1. Please identify:
      - The overall purpose of the code
      - Its main modules/classes/functions and their responsibilities
      - Any external dependencies or notable algorithms
   2. Format your answer as:
      - A one-sentence “Big Picture” overview
      - A bullet list of each major component with a 1–2 line description
      - A final “Notes” bullet with any assumptions or caveats
   3. Be concise: aim for **8–12 bullets** total.
   ```

4. **Save the summary**</br>
   Copy the model’s response into `pr_agent_config/repo_summary.txt` in your project root.
