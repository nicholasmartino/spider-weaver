from behave import *

from city.Network import Network
from features.utils.datautils import *
from learnkit.train.NetworkAnalysis import *

pd.set_option("display.max_columns", 10)
pd.set_option("display.width", 1000)


@given("{data_frame} data samples located within {city}")
def step_impl(context, data_frame, city):
    context.city = city
    data_gdf = read_feather(f"{context.city}/{data_frame}").to_crs(26910)
    boundary_gdf = read_feather(f"{context.city}/boundary").to_crs(26910)

    assert boundary_gdf is not None
    assert gdf_box_overlaps(boundary_gdf, data_gdf)
    overlay = gpd.overlay(data_gdf, boundary_gdf)

    if not hasattr(context, "data"):
        context.gdf_db = {}
    context.gdf_db[city] = boundary_gdf
    context.gdf_db[data_frame] = overlay.copy().reset_index(drop=True)
    pass


@step("the geometry data of {data_frame} is valid")
def step_impl(context, data_frame):
    if validate_geo_dataframe(context, data_frame):
        return
    raise AttributeError(data_frame)


@step("{series} is available in the {data_frame} data")
def step_impl(context, series, data_frame):
    validate_geo_dataframe(context, data_frame)
    assert (
        series in context.gdf_db[data_frame].columns
    ), f"Choose one of {list(context.gdf_db[data_frame].columns)}"
    context.gdf_db[data_frame] = context.gdf_db[data_frame].loc[:, [series, "geometry"]]
    pass


@then("calculate segment length, straightness for {network}")
def step_impl(context, network):
    assert context.gdf_db is not None
    calculator = NetworkMetricsCalculator(context.gdf_db[network]).calculate_metrics()
    save_feather(f"{context.city}/processed/{network}", calculator.gdf)
    pass


@then(
    "{operation} the {series} ({label}) within {radii} meters from {data_frame} to parcels via street network"
)
def step_impl(context, operation, series, label, radii, data_frame):
    boundary_gdf = context.gdf_db[context.city]
    parcel_gdf = gpd.overlay(get_sample_parcels(context.city), boundary_gdf)
    nodes_gdf = read_feather(f"{context.city}/network/street_node")
    links_gdf = read_feather(f"{context.city}/network/street_link")
    save_feature_dict(label, series, f"data/{context.city}/processed/feature_dict.json")

    target_gdf = context.gdf_db[data_frame].copy()
    target_gdf[label] = target_gdf[series]
    target_gdf = target_gdf.loc[:, [label, "geometry"]].copy()

    joined_gdf = parcel_gdf.copy()
    for radius in radii.split(", "):
        network = Network(nodes_gdf, links_gdf)
        analyst = SpatialAnalyst(parcel_gdf, target_gdf)
        network_analyst = SpatialNetworkAnalyst(analyst, network)
        joined_gdf = pd.concat(
            [
                joined_gdf,
                network_analyst.buffer_join_network(
                    radius=int(radius), operation=operation
                ),
            ],
            axis=1,
        ).drop_duplicates()
        joined_gdf = joined_gdf.loc[:, ~joined_gdf.columns.duplicated()].copy()
        save_feather(f"{context.city}/processed/samples/parcel", joined_gdf)
        gc.collect()
    pass
