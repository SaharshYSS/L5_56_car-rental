# Lab 5 — Reflection

**1. Which issues were the easiest to fix, and which were the hardest? Why?**

The easiest were the style and simple quality issues: unused `import json`, missing blank lines (E302), long lines (E501), `== True`, and missing docstrings. Each one is local, the tool tells you the exact line, and the fix cannot change behaviour. Renaming camelCase functions to snake_case was also mechanical.

The hardest were the security issues that needed a design change rather than a one-line edit. `exec()` in `applyPromo` could not just be deleted, because the feature still had to work, so I changed the input from a line of Python code to a validated discount percentage. The hard-coded admin password also needed a decision about where the secret should live (an environment variable). The logic bugs (double-booking, negative rental days, negative daily rate) were hard in a different way: no tool reported them, so I only found them by running the program and reading the output.

**2. Did the static analysis tools report any false positives? If so, describe one example.**

Not many in this file, but some findings are context-dependent:

- Bandit B311 (`random` is not cryptographically secure) would be a false positive for something like shuffling a demo list. For booking codes it is reasonable to fix, since predictable codes could be guessed.
- Bandit B324 (SHA-1) is labelled High, but the real risk depends on use. Here it hashes licence numbers, so moving to SHA-256 was right; SHA-1 for a non-security checksum would be acceptable with `usedforsecurity=False`.
- Pylint and Flake8 overlap (unused import, bare except, `== True` were reported by both), so the raw issue count overstates the number of distinct problems.

The bigger lesson was the opposite of a false positive: **false negatives**. None of the tools noticed that a car could be rented twice or that a booking could cost -9000.

**3. How would you integrate static analysis tools into your actual software development workflow?**

- **Locally:** run Flake8 and Pylint in the editor while coding, and add a `pre-commit` hook so Flake8, Pylint and Bandit run on changed files before every commit.
- **CI (e.g. GitHub Actions):** run all three on every push and pull request, and fail the build on any Bandit Medium/High finding, any Flake8 error, or a Pylint score below a threshold (e.g. 9.5).
- **Configuration:** keep tool settings in `pyproject.toml`/`.flake8` so the whole team uses the same rules, and only suppress a warning with an inline comment that explains why.
- **Alongside tests:** static analysis does not replace unit tests; the logic bugs in this lab would be caught by tests, not linters.

**4. What tangible improvements did you observe in the code quality, readability, or potential robustness after applying the fixes?**

- **Measured:** Pylint 4.94 → 10.00/10; Bandit 11 issues (2 High, 4 Medium) → 0; Flake8 25 → 0.
- **Security:** the SQL-injection demo lookup now returns `[]` instead of every customer's licence and phone number; staff input can no longer execute code; receipts are private (`-rw-------` instead of world-writable); there is no password in the source.
- **Robustness:** invalid input (unknown car, end date before start date, negative rate, double booking) now raises a clear `ValueError` instead of being silently accepted or crashing with a `KeyError`. `return_car` always returns a number.
- **Readability:** consistent snake_case names, docstrings on every function, named constants (`EXTRA_KM_LIMIT`, `EXTRA_KM_RATE`) instead of magic numbers, and PEP 8 formatting make the file much easier to review and maintain.
