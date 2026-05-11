# Blue-prince-data-analysis
A Python-based data pipeline and analytical engine for the indie game Blue Prince. Includes automated gameplay data ingestion, persistent SQLite storage, and statistical analysis of player behavior and strategy evolution

# Installation
1. Install Tesseract OCR (macOS):
	```bash
	brew install tesseract
	```

2. Create and activate a virtual environment:
	```bash
	python3 -m venv .venv
	source .venv/bin/activate
	```

3. Install Python dependencies:
	```bash
	pip install -r requirements.txt
	```

4. Run the manual data collection app:
	```bash
	cd src/data_pipeline
	streamlit run main_page_interface_capture.py
	```

This launches the main Streamlit page for manual data collection.

You can also run it from the project root:
	```bash
	streamlit run src/data_pipeline/main_page_interface_capture.py
	```

# Run Analysis Script
To run `ppp.py` without import errors, use one of these options:

1. From the project root:
	```bash
	PYTHONPATH=src python -m data_analysis.ppp
	```

2. From `src/data_analysis`:
	```bash
	PYTHONPATH=.. python ppp.py
	```
