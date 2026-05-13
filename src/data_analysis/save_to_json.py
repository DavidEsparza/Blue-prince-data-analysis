from pathlib import Path
import json

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data"


def write_json(file_name, payload, output_dir=OUTPUT_DIR):
    """Write JSON payload to disk with consistent formatting."""
    output_path = Path(output_dir) / file_name
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)


def dataframe_to_dict(df, orient="dict", round_digits=None):
    """Convert a DataFrame to a dict with optional rounding."""
    if round_digits is not None:
        df = df.round(round_digits)
    return df.to_dict(orient=orient)


def dataframe_to_json_payload(df, orient="dict", round_digits=None):
    """Alias for DataFrame conversion used by export functions."""
    return dataframe_to_dict(df, orient=orient, round_digits=round_digits)
