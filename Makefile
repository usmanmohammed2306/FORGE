.PHONY: format-check lint unit test release-verify

format-check:
	.venv/bin/ruff format --check forge tests benchmarks

lint:
	.venv/bin/ruff check forge tests benchmarks

unit:
	.venv/bin/pytest -q

test: format-check lint unit

release-verify:
	.venv/bin/forge release verify
