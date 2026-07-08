PYTHON_VERSION ?= 3.11

.PHONY: all
all: install qa unit-tests type-check docs-build build ##  Runs installation, QA, tests, type checking, docs-build, and packaging.

.PHONY: install
install: ## Synchronises the environment with uv and installs pre-commit hooks.
	@echo "🚀 Creating/updating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

.PHONY: qa
qa: ## Verifies lockfile consistency and runs pre-commit checks.
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "🚀 Linting code: Running pre-commit"
	@uv run --group qa pre-commit run --all-files

.PHONY: unit-tests
unit-tests: ## Runs local unit tests and doctests using pytest.
	@echo "🚀 Testing code: Running pytest with Python $(PYTHON_VERSION)"
	@uv run --group unit-tests --python=$(PYTHON_VERSION) pytest -vv --cov=. --cov-report=html

.PHONY: integration-tests
integration-tests: ## Runs integration tests using pytest.
	@echo "🚀 Testing minimum versions: Running pytest with Python $(PYTHON_VERSION)"
	@uv run --group integration-tests --python=$(PYTHON_VERSION) pytest -vv tests/integration_*.py README.md

.PHONY: ci-integration-tests
ci-integration-tests: ## Runs integration tests for GitHub CI using pytest.
	@echo "🚀 Testing minimum versions: Running pytest with Python $(PYTHON_VERSION)"
	@uv run --group integration-tests --python=$(PYTHON_VERSION) pytest -vv -m="not extra" tests/integration_*.py README.md

.PHONY: minver-tests
minver-tests: ## Tests the codebase against the minimum supported dependency versions.
	@echo "🚀 Testing minimum versions: Running pytest with Python $(PYTHON_VERSION)"
	@uv run --resolution lowest-direct --group unit-tests --python=$(PYTHON_VERSION) pytest -vv

.PHONY: type-check
type-check: ## Runs static type checks with mypy.
	@echo "🚀 Static type checking: Running mypy"
	@uv run --group type-check --python=$(PYTHON_VERSION) mypy .

.PHONY: docs-build
docs-build: ## Copies the README and builds HTML documentation with Sphinx.
	@echo "🚀 Building documentation: Running Sphinx"
	@cp README.md docs/
	@uv run --group docs-build make -C docs clean html

.PHONY: build
build: ## Cleans build paths, builds distribution packages, and verifies the package imports successfully.
	@echo "🚀 Building the package"
	@rm -rf build dist
	@uv build
	@echo "🚀 Verifying build artifact import"
	@uv run --no-project --python=$(PYTHON_VERSION) --with ./dist/ecmwf_datastores_client*.whl python -c "import ecmwf.datastores"

.PHONY: template-update
template-update: ## Synchronises the template with the base Cookiecutter using cruft.
	@echo "🚀 Updating template: Running cruft"
	@uvx cruft[pyproject] update -y

.PHONY: help
help: ## Displays all available Makefile targets.
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
