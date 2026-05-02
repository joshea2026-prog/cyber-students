from datetime import datetime

# Supported input date formats — both are common in Ireland
_DATE_INPUT_FORMATS = ['%d-%m-%Y', '%d/%m/%Y']

# Canonical storage format
_DATE_OUTPUT_FORMAT = '%d-%m-%Y'


def parse_date(value: str) -> str:
    """Parse and validate a date string in Irish format (DD-MM-YYYY or DD/MM/YYYY).

    Raises:
        ValueError: If the value is not a string, or does not match a
                    supported format, or represents an invalid calendar date."""
    if not isinstance(value, str):
        raise ValueError('Date of birth must be a string')

    for fmt in _DATE_INPUT_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime(_DATE_OUTPUT_FORMAT)
        except ValueError:
            continue

    raise ValueError(
        f'Date of birth must be in DD-MM-YYYY or DD/MM/YYYY format, got: {value!r}'
    )