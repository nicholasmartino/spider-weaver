import json
import os.path

from city.shapeutils.GeoDataFrameUtils import *
from geopandas import GeoDataFrame


def save_feather(path: str, gdf: GeoDataFrame) -> None:
    full_path = f"data/{path}.feather"
    if not os.path.exists(os.path.dirname(full_path)):
        os.makedirs(os.path.dirname(full_path))
    gdf.to_feather(full_path)
    assert os.path.exists(full_path)
    return


def read_feather(path: str) -> GeoDataFrame:
    full_path: str = f"data/{path}.feather"
    if not os.path.exists(full_path):
        raise FileNotFoundError(full_path)
    return read_gdf(full_path)


def get_sample_parcels(path: str) -> GeoDataFrame:
    processed_parcels_gdf_path = f"data/{path}/processed/samples/parcel.feather"
    if os.path.exists(processed_parcels_gdf_path):
        return read_gdf(processed_parcels_gdf_path)
    return read_gdf(f"data/{path}/parcel.feather")


def get_sample_rent_prices(path: str) -> GeoDataFrame:
    processed_rent_prices_gdf_path: str = f"data/{path}/processed/samples/rent_price.feather"
    if os.path.exists(processed_rent_prices_gdf_path):
        return read_gdf(processed_rent_prices_gdf_path)
    return read_gdf(f"data/{path}/rent_price.feather")


def get_assets_directory():
    return f"{os.path.expanduser('~')}/GitHub/phd-generative-city/assets"


def validate_geo_dataframe(context, data_frame: GeoDataFrame):
    assert context.gdf_db is not None
    assert context.gdf_db[data_frame] is not None
    assert context.gdf_db[data_frame].crs is not None
    assert True in list(context.gdf_db[data_frame].geometry.is_valid)
    context.gdf_db[data_frame]["perimeter"] = context.gdf_db[data_frame].geometry.length
    return True


def check_and_clean_path(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)
    if len(os.listdir(path)) > 0:
        for file in os.listdir(path):
            os.remove(f"{path}/{file}")


def read_feature_dict(path: str) -> dict:
    if not os.path.exists(path):
        return {}

    with open(path, "r") as file:
        data = json.load(file)

    return data


def save_feature_dict(key: str, value: str, path: str) -> bool:
    directory: str = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    data = {}
    if os.path.exists(path):
        with open(path, "r") as file:
            data = json.load(file)
    data[key] = value
    with open(path, "w") as file:
        json.dump(data, file)
    return os.path.exists(path)
