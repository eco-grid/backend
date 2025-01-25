.PHONY: freeze-requirements setup run clean

VENV_NAME = .venv
PYTHON = $(VENV_NAME)/bin/python
PIP = $(VENV_NAME)/bin/pip

freeze-requirements:
	source $(VENV_NAME)/bin/activate && pip freeze > requirements.txt

install:
	python3 -m venv $(VENV_NAME)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	make freeze-requirements

run:
	source $(VENV_NAME)/bin/activate && python -m flask run

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf $(VENV_NAME)
