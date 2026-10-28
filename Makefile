.PHONY: install test lint format network run init report sources monitor

install:
	uv sync

test:
	uv run pytest

network:
	uv run pytest -m network

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check . --fix

run:
	uv run streamlit run src/cofa_forward/ui/app.py

init:
	uv run python scripts/initialize_data.py

report:
	uv run python scripts/generate_report.py

sources:
	uv run python scripts/check_sources.py

monitor:
	uv run python scripts/monitor_bulletins.py
