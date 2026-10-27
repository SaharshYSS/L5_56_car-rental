# Lab 5 — Issues Found and Fixed (`car_rental.py`)

Line numbers refer to the **original** file. Ordered by severity (High → Medium → Low → style).

**Before:** Pylint 4.94/10 · Bandit 11 issues (2 High, 4 Medium, 5 Low) · Flake8 25 issues
**After:** Pylint 10.00/10 · Bandit 0 issues · Flake8 0 issues

## Security issues (Bandit)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| B103 Permissive file permissions (High) | Security | 67 | `os.chmod(path, 0o777)` makes every receipt readable and writable by any user on the machine | Set `0o600` so only the owner can read/write |
| B324 Weak hash SHA-1 (High) | Security | 48 | Licence numbers hashed with SHA-1, which is broken for collision resistance | Use `hashlib.sha256` |
| B608 SQL injection (Medium) | Security | 23, 26 | Queries built with `%` and `+` from user input. Demo `findCustomer("x' OR '1'='1")` returned **every** customer | Parameterised queries with `?` placeholders |
| B102 Use of `exec` (Medium) | Security | 53 | `applyPromo` runs any text typed by counter staff as Python code (arbitrary code execution) | Removed `exec`; promo is now a validated numeric discount percentage (0–100) |
| B306 Insecure `mktemp` (Medium) | Security | 63 | `tempfile.mktemp` has a race condition: another process can create the file first | `tempfile.mkstemp` (creates the file atomically) + `os.fdopen` |
| B101 `assert` for validation (Low) | Security / Bug | 30 | Asserts are stripped with `python -O`, so the customer check disappears | `if not ...: raise ValueError(...)` |
| B110 `try/except/pass` (Low) | Security / Bug | 41–42 | Bare `except: pass` silently swallows every error (returning an unknown car looked like success) | Validate plate and raise `ValueError` for unknown cars |
| B311 Insecure random (Low) | Security | 45 | `random` is predictable; booking codes could be guessed | `secrets.randbelow` |
| B105 / B107 Hard-coded password (Low) | Security | 70–71 | Admin password `admin@rent` is in source code and was the default argument, so `adminLogin("admin")` returned True | Password read from `RENTAL_ADMIN_PASSWORD` env var, no default, compared with `hmac.compare_digest` |

## Code quality issues (Pylint)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| W0102 Mutable default arg | Bug | 16 | `features=[]` is one list shared across every call | Default to `None`, create a new list inside the function |
| W0702 Bare except | Bug | 41 | Catches everything, including `KeyboardInterrupt` | Removed; explicit validation instead |
| R1710 Inconsistent returns | Bug | 16, 36 | `addCar` / `returnCar` sometimes return a value, sometimes `None` | Raise on invalid input; `return_car` always returns a number (0 when no extra km) |
| R1732 / W1514 File handling | Quality | 64 | `open()` without `with` (file leaks on error) and without encoding | `with os.fdopen(fd, "w", encoding="utf-8")` |
| W0611 Unused import | Quality | 2 | `json` imported but never used | Removed (also Flake8 F401) |
| W0122 exec-used | Security | 53 | Same as Bandit B102 | See above |
| C0103 Naming | Style | 16–75 | 13 functions in camelCase | Renamed to snake_case (`add_car`, `rent_car`, …) |
| C0114 / C0116 Docstrings | Style | 1, all functions | No module or function docstrings | Added docstrings |
| R1703 / R1705 | Quality | 57–60 | `if ...: return True else: return False` | `return bool(re.fullmatch(...))` |
| C0121 / C0206 | Quality | 77–78 | `== True` comparison; iterating dict keys then indexing | List comprehension over `fleet.items()` |
| C0209 / C0301 | Style | 23, 33, 65 | `%` formatting, lines over 100 chars | f-strings, wrapped lines |

## Style issues (Flake8)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| E302 / E305 | Style | 16–82, 101 | 1 blank line between top-level functions instead of 2 | Two blank lines around every top-level definition |
| E501 | Style | 19, 23, 31, 33, 65, 88–90 | Lines longer than 79 characters | Wrapped lines / introduced local variables |
| E722 | Style | 41 | Bare `except` | Removed (see Bandit B110) |
| E712 | Style | 78 | Comparison to `True` | `if car["available"]` |
| F401 | Style | 2 | Unused import `json` | Removed |

## Logic bugs found by running the program (no tool flagged these)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Double booking | Bug | 29–34 | Renting a car never marked it unavailable; the Swift was rented twice | Check `available`, set it to `False` on rent |
| Negative rental cost | Bug | 31 | End date before start date gave `Rent Innova: -9000` | Raise `ValueError` if `days <= 0` |
| Negative daily rate | Bug | 16, 85 | `addCar(..., -500)` was accepted | Reject rates `<= 0` and invalid plates in `add_car` |
| Unknown car | Bug | 29, 36 | `rentCar` crashed with `KeyError`; `returnCar` returned `None` silently | Explicit "Unknown car" `ValueError` |
| `available_cars` wrong | Bug | 75–80 | Rented cars were still listed as available (consequence of double-booking bug) | Fixed by tracking availability on rent/return |
| Module runs on import | Quality | 101 | `main()` ran whenever the module was imported | `if __name__ == "__main__": main()` |
