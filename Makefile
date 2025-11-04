.PHONY: install train serve lint format security-scan test audit frontend-install frontend-dev frontend-build openapi

install:
	pip install --upgrade pip
	pip install -r requirements-dev.txt
	cd frontend && npm install

train:
	python train_model.py

serve:
	uvicorn app:app --reload --port 8080

lint:
	ruff check .

format:
	ruff format .

security-scan:
	pip-audit
	safety check

test:
	pytest -q

audit:
	python -m pip_audit && safety check

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

openapi:
	python scripts/generate_openapi.py
