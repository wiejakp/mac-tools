# Adding a Script

1. Give the tool a single purpose and a descriptive root-level filename. Use POSIX shell for a small launcher and put reusable Python behavior in `src/local_scripts/`.
2. Support `--help`. For destructive operations, also provide `--dry-run`, an interactive choice and `--yes` for intentional automation. Do not schedule execution automatically.
3. Define the exact permitted filesystem root. Check containment before touching data, skip symlinks and cloud paths, and keep credentials out of terminal output and reports.
4. Test the tool with disposable fixtures inside `tests/`. Cover protected data, previews, partial failures and invalid arguments. Never test deletion on real applications.
5. Add the tool, its scope, requirements, invocation and report path to README. Keep reports and local settings ignored by Git.
6. Run `make verify`. Add any relevant syntax checks or targeted tests to the verification command.

Agent work belongs in this local repository. Adding an automation tool does not authorize sending data to hosted services, creating credentials, scheduling jobs, publishing the repository or changing other projects.
