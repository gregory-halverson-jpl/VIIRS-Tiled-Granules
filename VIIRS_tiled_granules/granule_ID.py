from os.path import basename
from datetime import date, datetime

def parse_VIIRS_product(granule_ID: str) -> str:
    """
    Extract the product name from a VIIRS granule_ID.

    Args:
        granule_ID (str): The VIIRS granule_ID.

    Returns:
        str: The product name extracted from the granule_ID.
    """
    return str(basename(granule_ID).split(".")[0])

def parse_VIIRS_date(granule_ID: str) -> date:
    """
    Extract the date from a VIIRS granule_ID and convert it to a date object.

    Args:
        granule_ID (str): The VIIRS granule_ID.

    Returns:
        date: The date extracted from the granule_ID.
    """
    return datetime.strptime(basename(granule_ID).split(".")[1][1:], "%Y%j").date()

def parse_VIIRS_tile(granule_ID: str) -> str:
    """
    Extract the tile identifier from a VIIRS granule_ID.

    Args:
        granule_ID (str): The VIIRS granule_ID.

    Returns:
        str: The tile identifier extracted from the granule_ID.
    """
    return str(basename(granule_ID).split(".")[2])

def parse_VIIRS_build(granule_ID: str) -> int:
    """
    Extract the build number from a VIIRS granule_ID and convert it to an integer.

    Args:
        granule_ID (str): The VIIRS granule_ID.

    Returns:
        int: The build number extracted from the granule_ID.
    """
    return int(basename(granule_ID).split(".")[3])