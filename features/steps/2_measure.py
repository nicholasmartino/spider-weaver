import geopandas as gpd
import pandas as pd
from behave import *
from city.Network import Network
from geopandas import GeoDataFrame

from features.utils.datautils import *
from features.utils.gcloudutils import *
from learnkit.train.NetworkAnalysis import *

pd.set_option("display.max_columns", 10)
pd.set_option("display.width", 1000)


@given("{data_frame} data located within {city}")
def step_impl(context: Context, data_frame: str, city: str):
    context.city = city
    bucket_id = get_bucket_id(city)
    context.bucket_id = bucket_id
    if not os.path.exists("data"):
        copy_gcs_path(bucket_id)
        
    feather_path = f"data/{bucket_id}/{data_frame}"
    data_gdf: GeoDataFrame = GeoDataFrame(read_feather(feather_path).to_crs(epsg=26910))
    boundary_gdf = GeoDataFrame(read_feather(f"data/{bucket_id}/open_street_map/boundary").to_crs(26910))

    assert boundary_gdf is not None
    assert gdf_box_overlaps(boundary_gdf, data_gdf)
    overlay = GeoDataFrame(gpd.overlay(data_gdf, boundary_gdf))

    if not hasattr(context, "data"):
        context.gdf_db = {}
    context.gdf_db[city] = boundary_gdf
    context.gdf_db[data_frame] = GeoDataFrame(overlay.copy().reset_index(drop=True))
    pass


@step("the geometry data of {data_frame} is valid")
def step_impl(context: Context, data_frame: str):
    if validate_geo_dataframe(context, data_frame):
        return
    raise AttributeError(data_frame)


@step("{series} is available in the {data_frame} data")
def step_impl(context: Context, series: str, data_frame: str):
    validate_geo_dataframe(context, data_frame)
    assert (
        series in context.gdf_db[data_frame].columns
    ), f"Choose one of {list(context.gdf_db[data_frame].columns)}"
    context.gdf_db[data_frame] = GeoDataFrame(context.gdf_db[data_frame].loc[:, [series, "geometry"]])
    pass


@then("calculate segment length, straightness for {network}")
def step_impl(context: Context, network: str):
    assert context.gdf_db is not None
    calculator = NetworkMetricsCalculator(context.gdf_db[network]).calculate_metrics()
    save_feather(f"data/{context.city}/spider_weaver/{network}", GeoDataFrame(calculator.gdf))
    pass

def get_output_path(context: Context, sample_path: str) -> str:
    return f"data/{context.bucket_id}/spider_weaver{sample_path.split(context.bucket_id)[1]}"

def get_sample_rent_prices_path(path: str) -> str:
    return f"data/{path}/craigslist/housing_rent.feather"

def get_sample_rent_prices(path: str) -> GeoDataFrame:
    processed_rent_prices_gdf_path: str = get_sample_rent_prices_path(path)
    if os.path.exists(processed_rent_prices_gdf_path):
        return read_gdf(processed_rent_prices_gdf_path)
    return read_gdf(f"data/{path}/rent_price.feather")


@then(
    "{operation} the {series} ({label}) within {radii} meters from {data_frame} to samples via street network"
)
def step_impl(context: Context, operation: str, series: str, label: str, radii: str, data_frame: str):
    boundary_gdf = GeoDataFrame(context.gdf_db[context.city])
    nodes_gdf = GeoDataFrame(read_feather(f"data/{context.bucket_id}/network/street_node"))
    links_gdf = GeoDataFrame(read_feather(f"data/{context.bucket_id}/network/street_link"))
    save_feature_dict(label, series, f"data/{context.bucket_id}/spider_weaver/feature_dict.json")

    sample_path = get_sample_rent_prices_path(context.bucket_id)
    output_path = get_output_path(context, sample_path)
    
    if os.path.exists(output_path):
        sample_gdf = GeoDataFrame(read_feather(output_path))
    else:
        print(f"Could not find {output_path}. Loading default from {sample_path}.")
        sample_gdf = GeoDataFrame(gpd.overlay(read_feather(sample_path), boundary_gdf))
        
    target_gdf = GeoDataFrame(context.gdf_db[data_frame].copy())
    target_gdf[label] = target_gdf[series]
    target_gdf = target_gdf.loc[:, [label, "geometry"]].copy()

    sample_gdf_copy = GeoDataFrame(sample_gdf.copy())
    for radius in radii.split(", "):
        network: Network = Network(nodes_gdf, links_gdf)
        analyst: SpatialAnalyst = SpatialAnalyst(sample_gdf, target_gdf)
        network_analyst: SpatialNetworkAnalyst = SpatialNetworkAnalyst(analyst, network)
        
        joined_buffer = network_analyst.buffer_join_network(radius=int(radius), operation=operation)
        joined_gdf = GeoDataFrame(pd.concat([ sample_gdf_copy, joined_buffer ], axis=1).drop_duplicates())
        joined_gdf = GeoDataFrame(joined_gdf.loc[:, ~joined_gdf.columns.duplicated()].copy())
        
        has_label = len([col for col in joined_gdf.columns if label in col and radii in col]) > 0
        has_value = len([col for col in joined_gdf.columns for value in target_gdf[label].unique() if str(value) in col and radii in col]) > 0
        assert has_label or has_value

        save_feather(output_path, joined_gdf)
        gc.collect()
        