import netrc
import os

import earthaccess

from .exceptions import *

__author__ = "Gregory H. Halverson, Evan Davis"

_AUTH = None

def authenticate(username: str = None, password: str = None) -> earthaccess.Auth:
    """
    Login to Earthdata using provided credentials, netrc credentials if available, 
    or falling back to environment variables.
    """
    # Only login to earthaccess once
    global _AUTH
    if _AUTH is not None:
        return _AUTH

    try:
        # Use provided username and password if available
        if username and password:
            _AUTH = earthaccess.login(strategy="provided", username=username, password=password)
            return _AUTH

        # Attempt to use netrc for credentials
        secrets = netrc.netrc()
        auth = secrets.authenticators("urs.earthdata.nasa.gov")
        if auth:
            _AUTH = earthaccess.login(strategy="netrc")  # Use strategy="netrc"
            return _AUTH

        # Fallback to environment variables if netrc fails
        if "EARTHDATA_USERNAME" in os.environ and "EARTHDATA_PASSWORD" in os.environ:
            _AUTH = earthaccess.login(strategy="environment")
            return _AUTH
        else:
            raise CMRServerUnreachable("Missing netrc credentials, environment variables 'EARTHDATA_USERNAME' and 'EARTHDATA_PASSWORD', or provided username and password")

    except Exception as e:
        raise CMRServerUnreachable(e)