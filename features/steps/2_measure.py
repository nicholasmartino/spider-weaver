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
        
    feather_path = f"{bucket_id}/{data_frame}"
    data_gdf: GeoDataFrame = GeoDataFrame(read_feather(feather_path).to_crs(epsg=26910))
    boundary_gdf = GeoDataFrame(read_feather(f"{bucket_id}/open_street_map/boundary").to_crs(26910))

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
    context.gdf_db[data_frame] = context.gdf_db[data_frame].loc[:, [series, "geometry"]]
    pass


@then("calculate segment length, straightness for {network}")
def step_impl(context: Context, network: str):
    assert context.gdf_db is not None
    calculator = NetworkMetricsCalculator(context.gdf_db[network]).calculate_metrics()
    save_feather(f"{context.city}/spider_weaver/{network}", calculator.gdf)
    pass


@then(
    "{operation} the {series} ({label}) within {radii} meters from {data_frame} to samples via street network"
)
def step_impl(context: Context, operation: str, series: str, label: str, radii: str, data_frame: str):
    boundary_gdf = GeoDataFrame(context.gdf_db[context.city])
    sample_gdf = GeoDataFrame(gpd.overlay(get_sample_rent_prices(context.bucket_id), boundary_gdf))
    nodes_gdf = GeoDataFrame(read_feather(f"{context.bucket_id}/network/street_node"))
    links_gdf = GeoDataFrame(read_feather(f"{context.bucket_id}/network/street_link"))
    save_feature_dict(label, series, f"output/{context.bucket_id}/spider_weaver/feature_dict.json")

    sample_path = get_sample_rent_prices_path(context.bucket_id)
    output_path = f"{context.bucket_id}/spider_weaver/{sample_path.split(context.bucket_id)[1]}"
    
    if os.path.exists(output_path):
        target_gdf = GeoDataFrame(read_feather(output_path))
    else:
        target_gdf = GeoDataFrame(context.gdf_db[data_frame].copy())

    target_gdf[label] = target_gdf[series]
    target_gdf = target_gdf.loc[:, [label, "geometry"]].copy()

    sample_gdf_copy = GeoDataFrame(sample_gdf.copy())
    for radius in radii.split(", "):
        network: Network = Network(nodes_gdf, links_gdf)
        analyst: SpatialAnalyst = SpatialAnalyst(sample_gdf, target_gdf)
        network_analyst: SpatialNetworkAnalyst = SpatialNetworkAnalyst(analyst, network)
        joined_gdf = GeoDataFrame(pd.concat(
            [
                sample_gdf_copy,
                network_analyst.buffer_join_network(
                    radius=int(radius), operation=operation
                ),
            ],
            axis=1,
        ).drop_duplicates())
        joined_gdf = GeoDataFrame(joined_gdf.loc[:, ~joined_gdf.columns.duplicated()].copy())

        assert len(joined_gdf.columns) > len(sample_gdf_copy.columns)
        assert len([col for col in joined_gdf.columns if label in col and radii in col]) > 0

        save_feather(output_path, joined_gdf)
        gc.collect()
        