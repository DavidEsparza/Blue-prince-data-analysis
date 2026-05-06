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

4. Run the collector:
	```bash
	python src/blue-prince-data-pipeline/run_collector.py
	```
