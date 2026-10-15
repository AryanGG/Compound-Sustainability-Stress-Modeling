.PHONY: reproduce test lint audit figures dashboard pdf ml ml-events ml-figures all

all: reproduce

reproduce:
	python run_v2.py --stage fit
	python run_v2.py --stage score --city all
	python -m audit.schema_check
	python -m src.analysis.run_compare && python -m src.analysis.run_sensitivity
	python -m src.analysis.run_validation && python -m src.analysis.run_archetypes
	python -m src.analysis.run_crosscity --cities mumbai coimbatore
	python -m src.analysis.run_figures && python scripts/check_claims.py && python scripts/lint_wording.py
	pytest -q

test:
	pytest -q

lint:
	python scripts/lint_wording.py
	python scripts/check_claims.py

audit:
	python -m audit.schema_check

figures:
	python -m src.analysis.run_figures

dashboard:
	python generate_report.py --city all

pdf:
	python scripts/generate_changes_pdf.py

ml-pipeline:
	python -m src.ml.predict_extreme_events --city all

ml-figures:
	python scripts/generate_event_figures.py

ml: ml-pipeline


