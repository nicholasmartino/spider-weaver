import math

import geopandas as gpd
import requests
import shapely.geometry as geometry
from scipy.spatial import Delaunay
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union


def get_geometries_gdf(elements):
    geometries = []
    for element in elements:
        if "geometry" in element:
            if element["type"] == "way":
                geom = LineString(
                    [(pt["lon"], pt["lat"]) for pt in element["geometry"]]
                )
            elif element["type"] == "node":
                geom = Point(element["lon"], element["lat"])
            elif element["type"] == "relation":
                geom = [
                    geometry.shape(member["geometry"])
                    for member in element["members"]
                    if "geometry" in member
                ]
                if geom:
                    geom = unary_union(geom)
            else:
                continue
            geometries.append(geom)
        elif "center" in element:
            geom = Point(element["center"]["lon"], element["center"]["lat"])
            geometries.append(geom)
    return gpd.GeoDataFrame({"geometry": geometries}, crs=4326)


def get_city_boundary_gdf(city):
    elements = query_elements_from_city_name(city, "boundary", "administrative")
    polygon = get_bounding_box(elements)
    return gpd.GeoDataFrame(
        {
            "geometry": [polygon],
        },
        crs=4326,
    )


def get_water_bodies_gdf(city):
    natural_tags = ["water", "bay", "strait", "coastline"]
    # waterway_tags = ["river", "riverbank", "canal", "stream"]
    elements = []
    [
        elements.extend(query_elements_from_city_name(city, "natural", tag))
        for tag in natural_tags
    ]
    # [
    #     elements.extend(query_elements_from_city_name(city, "waterway", tag))
    #     for tag in waterway_tags
    # ]
    return get_geometries_gdf(elements)


def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def get_natural_bounds(elements, tolerance=10):
    coordinates = []
    for element in elements:
        for member in element["members"]:
            if member["type"] == "node":
                coordinates.append([member["lon"], member["lat"]])
            elif member["type"] in ["way"]:
                coordinates += [
                    [pair["lon"], pair["lat"]] for pair in member["geometry"]
                ]

    triangulation = Delaunay(coordinates)

    # Step 2: Filter Triangles with Long Edges
    filtered_triangles = []
    for simplex in triangulation.simplices:
        pts = [coordinates[idx] for idx in simplex]
        edge_lengths = [distance(pts[i], pts[(i + 1) % 3]) for i in range(3)]
        if all(edge <= tolerance for edge in edge_lengths):
            filtered_triangles.append(pts)

    # Step 3: Merge Remaining Triangles
    polygons = [geometry.Polygon(triangle) for triangle in filtered_triangles]
    merged_shape = unary_union(polygons)

    # Step 4: Extract Outer Boundary
    outer_boundary = merged_shape.boundary
    return geometry.Polygon(outer_boundary)


def get_bounding_box(elements):
    bbox = elements[0]["bounds"]
    return get_polygon_from_bbox(bbox)


def get_polygon_from_bbox(bbox):
    min_lat, min_lon, max_lat, max_lon = (
        bbox["minlat"],
        bbox["minlon"],
        bbox["maxlat"],
        bbox["maxlon"],
    )
    return Polygon(
        [
            (min_lon, min_lat),
            (min_lon, max_lat),
            (max_lon, max_lat),
            (max_lon, min_lat),
            (min_lon, min_lat),
        ]
    )


def query_elements_from_city_name(city, key, value):
    overpass_url = "http://overpass-api.de/api/interpreter"

    # This query fetches the elements based on the key-value pair given the city name.
    overpass_query = f"""
    [out:json];
    area["name"="{city}"]->.searchArea;
    (
      way["{key}"="{value}"](area.searchArea);
      relation["{key}"="{value}"](area.searchArea);
      way["{key}"="{value}"](area.searchArea)->.a;
      (way.a(bn););
      relation["{key}"="{value}"](area.searchArea)->.b;
      (relation.b(bw););
    );
    out geom;
    """

    response = requests.get(overpass_url, params={"data": overpass_query})
    data = response.json()

    if not data["elements"]:
        print(Warning(f"No elements found for {key}={value} in {city}"))

    return data["elements"]
