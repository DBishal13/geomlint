"""geomlint — continuous validity, topology, and CRS-sanity checks for vector geospatial data.

The bet: geometry columns get treated as opaque blobs by every mainstream
data-observability tool. geomlint is the missing check suite — self-intersecting
polygons, duplicate vertices, missing/mismatched CRS declarations, and
coordinates that are quietly out of bounds for the CRS they claim.
"""

__version__ = "0.1.1"
