from typing import Union, List, Dict, Any
import logging
from datetime import datetime
from glob import glob
from os import makedirs
from os.path import exists, join, abspath, expanduser, basename, splitext
import json
import h5py
import numpy as np
import pandas as pd
from dateutil import parser
from matplotlib.colors import LinearSegmentedColormap
from shapely.geometry import Point, Polygon
from skimage.transform import resize

import colored_logging
import rasters
import rasters as rt
from modland import parsehv, generate_modland_grid

from rasters import Raster, RasterGrid, RasterGeometry

from .granule_ID import *

# Define colormaps for NDVI and Albedo
NDVI_COLORMAP = LinearSegmentedColormap.from_list(
    name="NDVI",
    colors=[
        "#0000ff",
        "#000000",
        "#745d1a",
        "#e1dea2",
        "#45ff01",
        "#325e32"
    ]
)

ALBEDO_COLORMAP = "gray"

DEFAULT_WORKING_DIRECTORY = "."

logger = logging.getLogger(__name__)

class VIIRSTiledGranule:
    """
    Class representing a VIIRS Granule.
    """

    def __init__(self, filename: str):
        """
        Initialize the VIIRSGranule object.

        :param filename: Path to the VIIRS granule file.
        """
        self._filename = filename
        self._cloud_mask = None

    def __repr__(self):
        """
        Return a string representation of the VIIRSGranule object.
        """
        display_dict = {
            "filename": self.filename
        }
        display_string = json.dumps(display_dict, indent=2)
        return display_string

    @property
    def filename(self) -> str:
        """
        Return the filename of the granule.
        """
        return self._filename
    
    @property
    def filename_absolute(self) -> str:
        """
        Return the absolute path of the filename.
        """
        return abspath(expanduser(self.filename))

    @property
    def filename_base(self) -> str:
        """
        Return the base name of the filename.
        """
        return basename(self.filename)

    @property
    def filename_stem(self) -> str:
        """
        Return the stem of the filename.
        """
        return splitext(self.filename_base)[0]

    @property
    def tile(self) -> str:
        """
        Return the tile information from the filename.
        """
        return parse_VIIRS_tile(self.filename)

    @property
    def hv(self) -> tuple:
        """
        Return the horizontal and vertical tile indices.
        """
        return parsehv(self.tile)

    @property
    def h(self) -> int:
        """
        Return the horizontal tile index.
        """
        return self.hv[0]

    @property
    def v(self) -> int:
        """
        Return the vertical tile index.
        """
        return self.hv[1]

    @property
    def date_UTC(self) -> datetime:
        """
        Return the date in UTC from the filename.
        """
        return datetime.strptime(self.filename_base.split(".")[1][1:], "%Y%j")

    @property
    def grids(self) -> List[str]:
        """
        Return the list of grids in the HDF5 file.
        """
        with h5py.File(self.filename_absolute, "r") as file:
            return list(file["HDFEOS/GRIDS/"].keys())

    def variables(self, grid: str) -> List[str]:
        """
        Return the list of variables in a specific grid.

        :param grid: The grid name.
        """
        with h5py.File(self.filename_absolute, "r") as file:
            return list(file[f"HDFEOS/GRIDS/{grid}/Data Fields/"].keys())
        
    def DN(self, variable: str, grid: str, geometry: RasterGeometry = None) -> Raster:
        with h5py.File(self.filename_absolute, "r") as file:
            dataset_name = f"HDFEOS/GRIDS/{grid}/Data Fields/{variable}"
            dataset = file[dataset_name]
            DN_geometry = generate_modland_grid(tile=self.tile, tile_size=dataset.shape[0])
            # TODO find a way to only load the pixels needed for the target geometry
            DN_array = np.array(dataset)
            DN = Raster(DN_array, geometry=DN_geometry)

        if geometry is not None:
            DN = DN.to_geometry(geometry)

        return DN
    
    def attributes(self, variable: str, grid: str) -> Dict:
        with h5py.File(self.filename_absolute, "r") as file:
            dataset_name = f"HDFEOS/GRIDS/{grid}/Data Fields/{variable}"
            dataset = file[dataset_name]
            attributes = dict(dataset.attrs)
        
        return attributes
    
    def layer(
            self, 
            variable: str, 
            grid: str,
            fill: int = None,
            scale: float = None,
            offset: float = None,
            valid_min: int = None,
            valid_max: int = None,
            geometry: RasterGeometry = None) -> Raster:
        DN = self.DN(
            variable=variable, 
            grid=grid,
            geometry=geometry
        )

        attributes = self.attributes(
            variable=variable,
            grid=grid
        )

        layer = DN

        if fill is None and "_Fillvalue" in attributes:
            fill = int(attributes["_Fillvalue"])

        if fill is not None:
            layer = rt.where(layer == fill, np.nan, layer)

        if valid_min is None and "valid_range" in attributes:
            valid_min = int(attributes["valid_range"][0])

        if valid_min is not None:
            layer = rt.where(layer < valid_min, np.nan, layer)

        if valid_max is None and "valid_range" in attributes:
            valid_max = int(attributes["valid_range"][1])

        if valid_max is not None:
            layer = rt.where(layer > valid_max, np.nan, layer)

        if scale is None and "scale_factor" in attributes:
            scale = float(attributes["scale_factor"])

        if scale is not None:
            layer *= scale
        
        if offset is None and "add_offset" in attributes:
            offset = float(attributes["add_offset"])
        
        if offset is not None:
            layer += offset

        return layer

    def fill(
            self, 
            variable: str, 
            grid: str, 
            fill: int = None,
            geometry: RasterGeometry = None) -> Raster:
        DN = self.DN(
            variable=variable, 
            grid=grid,
            geometry=geometry
        )

        attributes = self.attributes(
            variable=variable,
            grid=grid
        )

        layer = DN

        if fill is None and "_Fillvalue" in attributes:
            fill = int(attributes["_Fillvalue"])

        if fill is not None:
            layer = layer == fill
        else:
            layer = Raster(np.full(layer.shape, False), geometry=layer.geometry)
        
        return layer
