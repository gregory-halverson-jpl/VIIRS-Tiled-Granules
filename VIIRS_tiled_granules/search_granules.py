from typing import Union, List
from datetime import datetime, date
from dateutil import parser
import logging

import earthaccess

import colored_logging as cl
from rasters import Point, Polygon, RasterGeometry
from modland import generate_modland_grid

from .exceptions import *

__author__ = "Gregory H. Halverson, Evan Davis"

logger = logging.getLogger(__name__)

def earliest_datetime(date_in: Union[date, str]) -> datetime:
    """
    Convert a date or date string to the earliest datetime of that date.

    Args:
        date_in (Union[date, str]): The input date or date string.

    Returns:
        datetime: The earliest datetime of the input date.
    """
    if isinstance(date_in, str):
        datetime_in = parser.parse(date_in)
    else:
        datetime_in = date_in

    date_string = datetime_in.strftime("%Y-%m-%d")
    return parser.parse(f"{date_string}T00:00:00Z")


def latest_datetime(date_in: Union[date, str]) -> datetime:
    """
    Convert a date or date string to the latest datetime of that date.

    Args:
        date_in (Union[date, str]): The input date or date string.

    Returns:
        datetime: The latest datetime of the input date.
    """
    if isinstance(date_in, str):
        datetime_in = parser.parse(date_in)
    else:
        datetime_in = date_in

    date_string = datetime_in.strftime("%Y-%m-%d")
    return parser.parse(f"{date_string}T23:59:59Z")

def search_granules(
        concept_ID: str,
        date_UTC: Union[date, str] = None,
        start_date_UTC: Union[date, str] = None,
        end_date_UTC: Union[date, str] = None,
        geometry: Union[Point, Polygon, RasterGeometry] = None,
        tile: str = None,
        tile_size: int = None) -> List[earthaccess.search.DataGranule]:
    """
    Search for VIIRS granules within a specified date range and target geometry.

    Args:
        concept_ID (str): The concept ID for the granules.
        date_UTC (Union[date, str], optional): The specific date for the search.
        start_date_UTC (Union[date, str], optional): The start date for the search range.
        end_date_UTC (Union[date, str], optional): The end date for the search range.
        target_geometry (Union[Point, Polygon, RasterGeometry], optional): The target geometry for the search.
        tile (str, optional): The tile identifier for the granules.

    Returns:
        List[earthaccess.search.DataGranule]: A list of found granules.
    """
    # Parse date strings to date objects if necessary
    if isinstance(date_UTC, str):
        date_UTC = parser.parse(date_UTC).date()
    
    if isinstance(start_date_UTC, str):
        start_date_UTC = parser.parse(start_date_UTC).date()

    if isinstance(end_date_UTC, str):
        end_date_UTC = parser.parse(end_date_UTC).date()

    # Set start_date_UTC to date_UTC if start_date_UTC is not provided
    if start_date_UTC is None and date_UTC is not None:
        start_date_UTC = date_UTC

    # Set end_date_UTC to start_date_UTC if end_date_UTC is not provided
    if end_date_UTC is None:
        end_date_UTC = start_date_UTC

    if geometry is None and tile_size is None:
        raise ValueError("neither geometry nor tile size given")

    if geometry is None:
        geometry = generate_modland_grid(tile=tile, tile_size=tile_size)

    # Create the query with the concept ID and temporal range
    query = earthaccess.granule_query() \
        .concept_id(concept_ID) \
        .temporal(earliest_datetime(start_date_UTC), latest_datetime(end_date_UTC))

    # Add spatial constraints to the query if provided
    if isinstance(geometry, Point):
        # If the target geometry is a Point, add a point constraint to the query
        query = query.point(geometry.x, geometry.y)
    
    if isinstance(geometry, Polygon):
        # If the target geometry is a Polygon, add a polygon constraint to the query
        ring = geometry.exterior
        
        # Ensure the ring is counter-clockwise
        if not ring.is_ccw:
            ring = ring.reverse()
        
        coordinates = ring.coords
        
        # Add the polygon coordinates to the query
        query = query.polygon(coordinates)
    
    if isinstance(geometry, RasterGeometry):
        # If the target geometry is a RasterGeometry, add a polygon constraint to the query
        ring = geometry.corner_polygon_latlon.exterior
        
        # Ensure the ring is counter-clockwise
        if not ring.is_ccw:
            ring = ring.reverse()
        
        coordinates = ring.coords
        
        # Add the polygon coordinates to the query
        query = query.polygon(coordinates)
    
    # Add tile constraint to the query if provided
    if tile is not None:
        query = query.readable_granule_name(f"*.{tile}.*")

    # Execute the query and handle exceptions
    granules: List[earthaccess.search.DataGranule]
    try:
        granules = query.get()
    except Exception as e:
        raise CMRServerUnreachable(e)
    
    # Sort the granules by their beginning datetime
    granules = sorted(granules, key=lambda granule: granule["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"])

    # Log the found granules
    logger.info("Found the following granules for VIIRS 2 using the CMR search:")
    for granule in granules:
        logger.info("  " + cl.file(granule["meta"]["native-id"]))
    logger.info(f"Number of VIIRS 2 granules found using CMR search: {len(granules)}")

    return granules