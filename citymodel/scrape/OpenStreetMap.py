import math

import geopandas as gpd
import requests
import shapely.geometry as geometry
from scipy.spatial import Delaunay
from shapely.geometry import Polygon
from shapely.ops import unary_union


def get_city_boundary_gdf(city):
    elements = query_elements_from_city_name(city)
    polygon = get_bounding_box(elements)
    return gpd.GeoDataFrame({
        'geometry': [polygon],
    }, crs=4326)


def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def get_natural_bounds(elements, tolerance=10):
    coordinates = []
    for element in elements:
        for member in element['members']:
            if member['type'] == 'node':
                coordinates.append([member['lon'], member['lat']])
            elif member['type'] in ['way']:
                coordinates += [[pair['lon'], pair['lat']] for pair in member['geometry']]

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
    bbox = elements[0]['bounds']
    return get_polygon_from_bbox(bbox)


def get_polygon_from_bbox(bbox):
    min_lat, min_lon, max_lat, max_lon = bbox['minlat'], bbox['minlon'], bbox['maxlat'], bbox['maxlon']
    return Polygon([
        (min_lon, min_lat),
        (min_lon, max_lat),
        (max_lon, max_lat),
        (max_lon, min_lat),
        (min_lon, min_lat)
    ])


def query_elements_from_city_name(city):
    overpass_url = "http://overpass-api.de/api/interpreter"

    # This query fetches the boundary of the city given its name.
    overpass_query = f"""
    [out:json];
    area["name"="{city}"]->.searchArea;
    (
      relation["boundary"="administrative"]["name"="{city}"](area.searchArea);
    );
    out geom;
    """

    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()

    if not data['elements']:
        raise ValueError(f"No boundary found for {city}")

    return data['elements']
