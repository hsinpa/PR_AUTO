FILE_CRAWLER_SYSTEM_PROMPT = """\
Given a list of script file name and its dependency,
your job is to output the dependency's full path in github.
Only scripts under the same repository need to be capture.

For example
```
file name: src/model/pull_request_model.py

import asyncio
import re
from src.model.pull_request_model import FileModel
from src.utility.fetch_utility import fetch_github_file
```
In the example,
asyncio and re are third party package, so it is not part of local dependency file
you should catch src.model.pull_request_model and src.utility.fetch_utility as
src/model/pull_request_model.py
src/utility/fetch_utility.py

And the json format will be like
```
{{
    "file_path": "src/model/pull_request_model.py",
    "dependencies_path": ["src/model/pull_request_model.py", "src/utility/fetch_utility.py"]
}}
```

In actual environment, script file type is not always python, you should be prepare to face various type of programming langauge,
but you can use file type to deduce it's programming langauge.

When creating "dependencies_path", all folder name must exist on the "file_path" column.
Do not make up on your own.

Even if the script is import as relative path, you should still output in full path
"""

FILE_CRAWLER_HUMAN_PROMPT = """\
[File name and its dependencies]
'''
{file_dependency_paths_text}
'''

Output the dependency file path in the format of json array as below
```json
[
    {{
        "file_path": "the path of main file",
        "dependency_paths": [a list of dependency file paths]
    }}
]
```
"""
