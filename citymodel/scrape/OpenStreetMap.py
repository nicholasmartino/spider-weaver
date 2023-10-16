import geopandas as gpd
import requests
from shapely.geometry import Polygon


def get_city_boundary_gdf(city):
    elements = query_elements_from_city_name(city)
    polygon = get_bounding_box(elements)
    return gpd.GeoDataFrame({
        'geometry': [polygon],
    }, crs=4326)


def get_bounding_box(elements):
    bbox = elements[0]['bounds']
    min_lat, min_lon, max_lat, max_lon = bbox['minlat'], bbox['minlon'], bbox['maxlat'], bbox['maxlon']
    polygon = Polygon([
        (min_lon, min_lat),
        (min_lon, max_lat),
        (max_lon, max_lat),
        (max_lon, min_lat),
        (min_lon, min_lat)
    ])
    return polygon


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
