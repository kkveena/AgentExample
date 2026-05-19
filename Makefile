.PHONY: install install-dev test test-cov lint notebook eval clean

PYTHON ?= python3
PIP ?= pip

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

test:
	PYTHONPATH=src $(PYTHON) -m pytest tests -q

test-cov:
	PYTHONPATH=src $(PYTHON) -m pytest tests --cov=settlement_agent --cov-report=term-missing

eval:
	PYTHONPATH=src $(PYTHON) -m settlement_agent.application.evaluation_service.eval_runner

notebook:
	PYTHONPATH=src $(PYTHON) -m jupyter notebook notebook/phase1_firm_short_reference_workflow.ipynb

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf build dist *.egg-info
