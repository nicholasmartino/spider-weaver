import geopandas as gpd
import requests
from behave import *
from lxml import etree
from shapely.geometry import Point

from citymodel.scrape.OpenStreetMap import get_city_boundary_gdf


def download_and_save_gps_traces(place_name):
    boundary = get_city_boundary_gdf(place_name)

    # Fetch GPS data from OSM API
    bbox = "<define_your_bbox_here>"  # Define the bounding box for the place
    url = f"https://api.openstreetmap.org/api/0.6/trackpoints?bbox={bbox}&page=0"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch GPS data for {place_name}")

    # Parse the XML data
    root = etree.fromstring(response.content)
    points = []
    for point in root.findall('.//trkpt'):
        lat = float(point.get('lat'))
        lon = float(point.get('lon'))
        points.append(Point(lon, lat))

    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=points, crs="EPSG:4326")  # GPS data is usually in WGS 84 (EPSG:4326)

    # Convert the CRS to EPSG:26910
    gdf.to_crs(epsg=26910, inplace=True)

    # Save to .feather file
    gdf.reset_index(drop=True).to_feather(f"{place_name}_gps_traces.feather")
    return


@given('a valid identification of a {place_name}')
def step_given_valid_place_name(context, place_name):
    context.place_name = place_name


@then('download and save GPS traces')
def step_then_download_and_save(context):
    download_and_save_gps_traces(context.place_name)
