<!-- source: ../PioneerSP16Review/AGENTS.md | scrubbed -->

# Workspace boundaries

- Treat `` as read-only. Do not edit, create, delete, or otherwise modify files or Git state there.
- Write only instructions for yourself in `Review`, including prompts describing proposed changes for the main SP16 project.
- Local Git administration in the review folder is permitted, including `.gitignore` maintenance, repository initialization, staging, commits, and local branches. This exception does not authorize project implementation or changes to the main SP16 project.
- Do not implement project changes in either folder. When a change is needed, prepare a concrete prompt for the main SP16 project to carry out.
- Avoid commands that could write to the main project, including tests, builds, formatters, package installation, and Git mutations, unless they are demonstrably read-only.
- Do not send a prepared prompt to another chat unless the user explicitly authorizes sending it.
