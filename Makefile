.PHONY: install demo sample full test database
install:
	python -m pip install -r requirements.txt
demo:
	python src/run_pipeline.py --mode sample --fixture
sample:
	python src/run_pipeline.py --mode sample
full:
	python src/run_pipeline.py --mode full
test:
	python -m pytest -q
database:
	docker compose up -d --wait
