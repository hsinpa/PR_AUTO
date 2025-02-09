def is_python_diff_header(header_line):
    """
    Check if a diff header (starting with "diff --git")
    refers to a Python file.

    The header line typically looks like:
      diff --git a/path/to/file.py b/path/to/file.py
    """
    parts = header_line.split()
    # We expect at least: ['diff', '--git', 'a/file', 'b/file']
    if len(parts) < 4:
        return False

    # Extract file paths and remove the "a/" or "b/" prefix
    file_a = parts[2][2:] if parts[2].startswith("a/") else parts[2]
    file_b = parts[3][2:] if parts[3].startswith("b/") else parts[3]

    return file_a.endswith('.py') or file_b.endswith('.py')


def filter_patch(patch_lines):
    """
    Process the patch lines and return only those parts
    corresponding to diff blocks for .py files.

    It also preserves any commit metadata (the header section)
    that comes before the first diff block.
    """
    filtered_output = []
    diff_block = []  # Hold lines for the current diff block
    inside_diff = False  # Are we currently inside a diff block?
    include_block = False  # Should the current block be included?

    header_lines = []  # Lines before the first "diff --git" (commit metadata)

    for line in patch_lines:
        if line.startswith("diff --git"):
            # If we were processing a previous diff block, decide if we want to output it.
            if inside_diff:
                if include_block:
                    filtered_output.extend(diff_block)
                diff_block = []
            inside_diff = True
            diff_block.append(line)
            include_block = is_python_diff_header(line)
        else:
            if inside_diff:
                diff_block.append(line)
            else:
                # Lines outside any diff block (usually commit metadata)
                header_lines.append(line)

    # Flush the last diff block if applicable
    if inside_diff and include_block:
        filtered_output.extend(diff_block)

    # If we have any allowed diff blocks, prepend the commit header
    if filtered_output:
        return header_lines + filtered_output
    else:
        return []

