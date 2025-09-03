from src.model.pull_request_model import PullRequestIssueModel
from src.utility.utility_func import get_priority_markdown
import re


def get_custom_instruction(c_instruction: str) -> str:
    if c_instruction == '':
        return ''

    return f"""[Instruction]
Strictly follow the instruction
```
{c_instruction}
```\
"""


def get_comment_content(title: str, priority: str, content: str) -> str:
    issue_text = f'''### Issue: {title}
{get_priority_markdown(priority)}

{content}'''

    return issue_text

def git_patches_to_text(patch_contents: list[str]):
    text = ''

    for index, patch in enumerate(patch_contents):
        text += f'''Section index {index}:
====== Start of PR section index {index} ======
{patch}
====== End of PR section index {index} ======\n\n'''

    return text

def split_git_patches(patch_content: str, file_extensions: list = None):
    """
    Split a multi-commit git patch into individual text sections,
    optionally filtering by file extensions (case-insensitive).
    """
    # Allow uppercase hex; keep multiline split
    pattern = r'(?=^From\s+[a-fA-F0-9]{40}\b)'
    patches = re.split(pattern, patch_content, flags=re.MULTILINE)
    patches = [patch.strip() for patch in patches if patch.strip()]

    if not file_extensions:
        return patches

    filtered_patches = []
    for patch in patches:
        filtered_patch = filter_patch_by_extensions(patch, file_extensions)
        if filtered_patch:  # keep only if there are relevant file changes
            filtered_patches.append(filtered_patch)
    return filtered_patches


def _norm_exts(exts):
    # normalize to ".ext" and lowercase
    return tuple((e if e.startswith('.') else f'.{e}').lower() for e in exts)


def filter_patch_by_extensions(patch: str, file_extensions: list):
    """
    Keep only the diff sections in a single commit whose file paths end with target extensions.
    Returns None if no matching sections are found.
    """
    lines = patch.split('\n')

    # Find first diff section
    diff_start_idx = None
    for i, line in enumerate(lines):
        if line.startswith('diff --git'):
            diff_start_idx = i
            break

    # If no diff content, drop this patch entirely
    if diff_start_idx is None:
        return None

    header_lines = lines[:diff_start_idx]
    remaining_content = '\n'.join(lines[diff_start_idx:])
    diff_sections = re.split(r'(?=^diff --git )', remaining_content, flags=re.MULTILINE)
    diff_sections = [s.strip() for s in diff_sections if s.strip()]

    norm_exts = _norm_exts(file_extensions)
    filtered_sections = [s for s in diff_sections if should_include_diff_section(s, norm_exts)]

    if not filtered_sections:
        return None

    # Rebuild commit: header + filtered diffs
    return '\n'.join(header_lines + [''] + filtered_sections).strip()


def should_include_diff_section(diff_section: str, norm_exts: tuple[str, ...]):
    """
    Return True if the per-file diff's path ends with one of norm_exts.
    Looks at the 'diff --git a/... b/...' line; ignores /dev/null.
    """
    # First line of the section should be: diff --git a/<path> b/<path>
    first_line = diff_section.split('\n', 1)[0]
    m = re.match(r'^diff --git a/(.+?) b/(.+)$', first_line)
    if not m:
        return False

    file_a, file_b = m.groups()

    for p in (file_a, file_b):
        if p == '/dev/null':
            continue
        if p.lower().endswith(norm_exts):
            return True
    return False