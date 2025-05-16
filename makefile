.PHONY: init init-dev lint mypy tests check

init:
	python -m pip install --upgrade pip
	pip install "poetry>=2.0"
	poetry install

init-dev: init
	poetry install --with dev

lint:
	poetry run ruff check

build: init
	poetry build

mypy:
	poetry run mypy ctreepo
	poetry run mypy tests

tests:
	poetry run pytest -vv

check: lint mypy tests
	@echo "✅ Проверки пройдены"
