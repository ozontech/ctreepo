.PHONY: init init-dev build lint mypy check

init:
	pip install poetry
	poetry install --without dev

init-dev: init
	poetry install --with dev

build: init
	poetry build

lint:	
	poetry run black --check src tests
	poetry run ruff check src tests

mypy:
	poetry run mypy src tests

test:
	poetry run pytest \
	--cov src \
	--cov-report term \
	--cov-report html \
	--cov-report xml:coverage.xml \
	--cov-fail-under=80

format:
	poetry run ruff check src tests --select F401,UP035,I001 --fix
	poetry run black src tests
	
check: format lint mypy test
	@echo "✅ Проверки пройдены"
