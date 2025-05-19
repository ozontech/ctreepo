.PHONY: init init-dev lint mypy tests check

init:
	python -m pip install --upgrade pip
	pip install "poetry>=2.0"
	poetry install --without dev
	poetry --version

init-dev: init
	poetry install --with dev

lint:
	poetry run ruff check ctreepo tests examples

build: init
	poetry build

mypy:
	poetry run mypy ctreepo tests
test:
	poetry run pytest -vv

check: lint mypy test
	@echo "✅ Проверки пройдены"
