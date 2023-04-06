SHELL:=/usr/bin/env bash

.PHONY: lint
lint:
	poetry run mypy pytest_qaseio

.PHONY: package
package:
	poetry check
	poetry run pip check
	poetry run safety check --full-report

.PHONY: check
check: lint package

.PHONY: run-hooks
run-hooks:
	pre-commit run --hook-stage push --all-files
