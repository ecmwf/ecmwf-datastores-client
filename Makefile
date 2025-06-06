PROJECT := ecmwf.datastores
CONDA := conda
CONDAFLAGS :=
COV_REPORT := html

default: qa unit-tests type-check

qa:
	pre-commit run --all-files

unit-tests:
	python -m pytest -vv --cov=. --cov-report=$(COV_REPORT)

type-check:
	python -m mypy .

conda-env-update:
	$(CONDA) install -y -c conda-forge conda-merge
	$(CONDA) run conda-merge environment.yml ci/environment-ci.yml > ci/combined-environment-ci.yml
	$(CONDA) env update $(CONDAFLAGS) -f ci/combined-environment-ci.yml

docker-build:
	docker build -t $(PROJECT) .

docker-run:
	docker run --rm -ti -v $(PWD):/srv $(PROJECT)

template-update:
	pre-commit autoupdate --repo https://github.com/kynan/nbstripout
	pre-commit run --all-files cruft -c .pre-commit-config-cruft.yaml

docs-build:
	cp README.md docs/. && cd docs && rm -fr _api && make clean && make html

# DO NOT EDIT ABOVE THIS LINE, ADD COMMANDS BELOW

integration-tests:
	python -m pytest -vv --cov=. --cov-report=$(COV_REPORT) tests/integration*.py

doc-tests:
	python -m pytest -vv --doctest-glob='*.md' README.md

all-tests: unit-tests integration-tests doc-tests

ci-integration-tests: unit-tests doc-tests
	python -m pytest -vv --cov=. -m="not extra" --cov-report=$(COV_REPORT) tests/integration*.py
