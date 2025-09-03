CODE_REVIEW_RULE = """\
# Code Structure & Organization
Single Responsibility: Does each function/class have a clear, single purpose?
DRY Principle: Are there repeated code blocks that should be extracted into reusable functions?
Naming Conventions: Are variables, functions, and classes named clearly and consistently?
Code Modularity: Is the code properly organized into logical modules/components?

# Side Effects & State Management
Pure Functions: Are functions free from unexpected side effects?

# Technical Debt
TODO/FIXME Comments: Are temporary fixes properly documented with clear next steps?
Code Complexity: Is the code unnecessarily complex or could it be simplified?
Design Patterns: Are appropriate design patterns used correctly?

# Performance Considerations
## CPU Usage
Algorithm Efficiency: Are algorithms optimized for the expected data size?
Loop Optimization: Are loops efficient and avoid unnecessary iterations?
Recursive Functions: Do recursive functions have proper base cases and won't cause stack overflow?
Computation Complexity: Is the time complexity reasonable (O(n), O(log n), etc.)?

## Memory Management
Memory Leaks: Are objects properly disposed/garbage collected?
Large Data Structures: Are large arrays/objects handled efficiently?
Caching Strategy: Is caching used appropriately without over-caching?
Resource Cleanup: Are file handles, database connections, etc. properly closed?

## Potential Freeze/Blocking Issues
Async Operations: Are long-running operations properly asynchronous?
UI Thread Blocking: Does the code avoid blocking the main/UI thread?
Database Queries: Are database operations optimized and non-blocking?
Network Requests: Are API calls handled with proper timeouts and error handling?

# Security & Error Handling
## Security

Input Validation: Are all user inputs properly validated and sanitized?
SQL Injection: Are database queries parameterized to prevent injection?
XSS Prevention: Is user-generated content properly escaped for display?
Authentication/Authorization: Are security checks in place where needed?

## Error Handling
Exception Handling: Are exceptions caught and handled appropriately?
Error Messages: Are error messages helpful but not revealing sensitive information?
Graceful Degradation: Does the system handle failures gracefully?
Logging: Are important events and errors properly logged?\
"""

PLAN_SYSTEM_PROMPT = f"""\
You are a professional code programmer and github pr reviewer.
You will provide useful feedback on the pr patch content.
Only focus on the quality of code, ignore metadata\
"""

PLAN_HUMAN_PROMPT = """\
The title of this issue is '{title}'

[PR PATCH]
'''
{pr_patch}
'''

{custom_instruction}

[Issue]
'''
{issue}
'''

[Full target script]
'''
{file_script}
'''

[Dependency file script]
'''
{dependency_script}
'''

[Code review rule] is a more general rule, and [Instruction] will include more specific style/rule for this project.

Focus on [Issue],
[PR PATCH] show you what has change that cause the [Issue].
The full script of target file and its dependency is given.
Use them as supplement material, so you have enough information exploit possible cause of issue 

Output
"""
