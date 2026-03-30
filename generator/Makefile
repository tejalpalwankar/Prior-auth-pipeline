generate:
	python3 generator/generate_pa_data.py

load:
	python3 generator/load_to_duckdb.py

run:
	python3 generator/generate_pa_data.py
	python3 generator/load_to_duckdb.py

app:
	streamlit run streamlit_app/app.py

docs:
	cd dbt_project && dbt docs generate && dbt docs serve
