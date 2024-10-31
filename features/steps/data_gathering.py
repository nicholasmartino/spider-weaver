import datetime
import math
import os.path
from itertools import product

import matplotlib.pyplot as plt

import geopandas as gpd
import requests
from behave import *
from geopy.distance import geodesic
from lxml import etree
from shapely.geometry import Point

from citymodel.scrape.OpenStreetMap import get_city_boundary_gdf, get_water_bodies_gdf


def split_bbox(total_bounds, max_size=0.25):
    """Split the bounding box into smaller boxes within the maximum size limit."""
    min_lon, min_lat, max_lon, max_lat = total_bounds
    lon_steps = int((max_lon - min_lon) // max_size) + 1
    lat_steps = int((max_lat - min_lat) // max_size) + 1

    for i, j in product(range(lon_steps), range(lat_steps)):
        new_min_lon = min_lon + i * max_size
        new_min_lat = min_lat + j * max_size
        new_max_lon = min(new_min_lon + max_size, max_lon)
        new_max_lat = min(new_min_lat + max_size, max_lat)
        yield new_min_lon, new_min_lat, new_max_lon, new_max_lat


def download_and_save_gps_traces(place_name):
    nsmap = {"gpx": "http://www.topografix.com/GPX/1/0"}
    boundary = get_city_boundary_gdf(place_name)
    output_path = f"data/{place_name}/open_street_map/gps_traces.feather"
    max_page = 30

    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    gdf = gpd.GeoDataFrame(
        columns=[
            "box_id",
            "page",
            "segment_id",
            "point_id",
            "time",
            "speed",
            "geometry",
        ],
        geometry="geometry",
        crs="EPSG:4326",
    )  # GPS data is usually in WGS 84 (EPSG:4326)

    if os.path.exists(output_path):
        gdf = gpd.read_feather(output_path)

    existing_points = set(gdf["geometry"].apply(lambda geom: (geom.x, geom.y)))

    for i, bbox in enumerate(split_bbox(boundary.total_bounds)):
        bbox_string = ",".join(map(str, bbox))
        page = 0

        while True:
            if page > max_page:
                break

            if (i in list(gdf["box_id"])) & (
                page in list(gdf[gdf["box_id"] == i]["page"])
            ):
                page += 1
                continue

            print(f"bbox#{i} [{bbox_string}], page#{page}")
            save = False
            url = f"https://api.openstreetmap.org/api/0.6/trackpoints?bbox={bbox_string}&page={page}"
            response = requests.get(url)
            if response.status_code != 200:
                print(
                    f"Warning: Failed to fetch GPS data for {bbox_string} with status code {response.status_code}"
                )
                break

            root = etree.fromstring(response.content)
            if not root.findall(".//gpx:trkpt", namespaces=nsmap):
                break

            for j, trkseg in enumerate(root.findall(".//gpx:trkseg", namespaces=nsmap)):
                previous_point = None
                previous_time = None

                for k, trkpt in enumerate(
                    trkseg.findall(".//gpx:trkpt", namespaces=nsmap)
                ):

                    lat = float(trkpt.get("lat"))
                    lon = float(trkpt.get("lon"))
                    current_point = Point(lon, lat)

                    if (lon, lat) in existing_points:
                        continue

                    time_element = trkpt.find(".//gpx:time", namespaces=nsmap)
                    current_time = None
                    speed = None

                    if time_element is not None:
                        current_time = datetime.datetime.fromisoformat(
                            time_element.text.replace("Z", "+00:00")
                        )

                    if previous_point is not None and previous_time is not None:
                        speed = calculate_speed(
                            previous_point, current_point, previous_time, current_time
                        )

                    index = len(gdf)
                    gdf.at[index, "box_id"] = i
                    gdf.at[index, "page"] = page
                    gdf.at[index, "segment_id"] = j
                    gdf.at[index, "point_id"] = k
                    gdf.at[index, "time"] = current_time
                    gdf.at[index, "speed"] = speed
                    gdf.at[index, "geometry"] = current_point
                    gdf.at[index, "count"] = 1

                    previous_point = current_point
                    previous_time = current_time
                    save = True

            if save:
                gdf.reset_index(drop=True).to_feather(output_path)

            page += 1  # Increment page number for the next request


def download_and_save_water_bodies(place_name):
    gdf = get_water_bodies_gdf(place_name)
    _, ax = plt.subplots()
    gdf.plot(ax=ax)
    plt.savefig(f"data/{place_name}/open_street_map/water_bodies.png")
    gdf.to_feather(f"data/{place_name}/open_street_map/water_bodies.feather")
    return


def calculate_speed(point1, point2, time1, time2):
    # Calculate the distance in kilometers
    distance = geodesic((point1.y, point1.x), (point2.y, point2.x)).kilometers
    # Calculate the total seconds
    time_delta = (time2 - time1).total_seconds()
    # Speed = distance / time in hours
    if time_delta != 0:
        speed = distance / (time_delta / 3600)  # Speed in km/h
        return speed
    return math.inf


@given("a valid place name {place_name}")
def step_given_valid_place_name(context, place_name):
    context.place_name = place_name


@then("download and save GPS traces")
def step_then_download_and_save(context):
    download_and_save_gps_traces(context.place_name)


@then("download and save water bodies")
def step_then_download_and_save_water_bodies(context):
    download_and_save_water_bodies(context.place_name)
