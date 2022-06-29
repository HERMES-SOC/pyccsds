# Licensed under a 3-clause BSD style license - see LICENSE.txt

"""
IO Interface for Reading CCSDS Data in Python.

pyccsds is a Python package developed at Southwest Research Institute
that provides an IO interface for reading CCSDS data.  The work
is based upon ccsdspy from Daniel DaSilva, with some variation.

This is an attempt to build the suite of tools which can interact
with the CCSDS space packet protocol based upon the flight software
documentation provided by the various instrument teams.
"""

# see license/LICENSE.rst

try:
    from .version import __version__
except ImportError:
    __version__ = "unknown"

# For egg_info test builds to pass, put package imports here.

from .interface import (Packet, PacketField, ParseMultiplePackets)
from .decode import (_decode_packet)



