# Module Overview: CI/CD Pipeline (GitHub Actions)
*Written and updated 25/03-2026 by Johnny* 

## What is our CI Pipeline?
In a collaborative data platform project, code stability is not just important, it is critical. Our Continuous Integration (CI) pipeline acts as an automated gatekeeper (powered by GitHub Actions), triggered every time a team member pushes code or creates a Pull Request against our `main` branch.

The primary purpose of the CI pipeline is to eliminate the classic *"It works on my machine"* syndrome and ensure that all code reaching production meets the highest quality standards.

### Architecture & Execution Flow
The pipeline runs on an isolated Ubuntu runner in the cloud `runs-on: ubuntu-latest` and executes the following steps sequentially using a Fail-Fast methodology:

1. **Environment Setup:** Checks out the repository and installs `uv` (an extremely fast, Rust-based package manager), setting up the Python 3.12 environment.

2. **Dependency Management:** Executes `uv sync` to install an exact mirror of the project's dependencies (FastAPI, Psycopg, Pytest, Ruff, etc)

3. **Code Review (Linting & Formatting):** Runs `Ruff` to analyze the code for anti-patterns and unused imports. It rigorously verifies that the code adheres to project formatting standards `PEP8`. If the code is poorly formatted, the pipeline fails, forcing the developer to format before merging.

4. **Unit Testing:** If the code passes the linter, `Pytest` executes our test suite against the `src/test/` directory, validating Pydantic models and running mocked API tests and unit testing. 

## Business Value & Impact

* **Psychological Safety:** Developers can code faster and experiment freely, knowing the automated pipeline will catch syntax errors or formatting issues before they can break the `main` branch.

* **Time Efficiency:** Code Reviews (PRs) can focus entirely on *business logic* and architectural decisions, rather than wasting time looking for missing commas or unused imports. The robot does the tedious work.

* **Idempotency & Quality Assurance:** Because the environment is built from scratch on every run, we mathematically prove that our code is fully containerizable and not reliant on hidden local environment variables.