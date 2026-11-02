"""
utils/labels.py — display names for the six criteria.

The one place the UI turns a criterion key into words. Display only: data values
and export column names keep the raw keys.
"""

CRITERION_LABELS = {
    "slope": "Slope",
    "rainfall": "Rainfall",
    "drainage": "Drainage density",
    "soil": "Soil texture",
    "lulc": "Land cover",
    "population": "Settlement proximity",
}


def criterion_label(key: str) -> str:
    return CRITERION_LABELS.get(key, str(key).capitalize())
