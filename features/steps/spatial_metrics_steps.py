import os.path

from behave import *

from citymodel.scrape.OpenStreetMap import get_city_boundary_gdf
from learnkit.train.NetworkAnalysis import *
from shapeutils.GeoDataFrameUtils import *
from citymodel.base.Network import Network


def save_feather(path, gdf):
	full_path = f"data/{path}.feather"
	if not os.path.exists(os.path.dirname(full_path)):
		os.makedirs(os.path.dirname(full_path))
	gdf.to_feather(full_path)
	assert (os.path.exists(full_path))
	return


def read_feather(path):
	full_path = f"data/{path}.feather"
	if not os.path.exists(full_path):
		raise FileNotFoundError(full_path)
	return read_gdf(full_path)


def get_parcel_gdf(path):
	processed_parcels_gdf_path = f"{path}/parcel"
	if os.path.exists(processed_parcels_gdf_path):
		return read_feather(processed_parcels_gdf_path)
	return read_feather(f"{path}/parcel")


def validate_geo_dataframe(context, data_frame):
	assert (context.gdf_db is not None)
	assert (context.gdf_db[data_frame] is not None)
	assert (context.gdf_db[data_frame].crs is not None)
	assert (True in list(context.gdf_db[data_frame].geometry.is_valid))
	return True


@given("{data_frame} data located within {city}")
def step_impl(context, data_frame, city):
	context.city = city
	data_gdf = read_feather(f"{context.city}/{data_frame}")
	boundary_gdf = get_city_boundary_gdf(city).to_crs(26910)
	assert (boundary_gdf is not None)
	assert (gdf_box_overlaps(boundary_gdf, data_gdf))

	if not hasattr(context, 'data'):
		context.gdf_db = {}
	context.gdf_db[city] = boundary_gdf
	context.gdf_db[data_frame] = data_gdf
	pass


@step("the geometry data of {data_frame} is valid")
def step_impl(context, data_frame):
	if validate_geo_dataframe(context, data_frame):
		return
	raise AttributeError(data_frame)


@step("{series} is available in the {data_frame} data")
def step_impl(context, series, data_frame):
	validate_geo_dataframe(context, data_frame)
	assert (series in context.gdf_db[data_frame].columns)
	pass


@then("calculate segment length, straightness for {network}")
def step_impl(context, network):
	assert(context.gdf_db is not None)
	calculator = NetworkMetricsCalculator(context.gdf_db[network]).calculate_metrics()
	save_feather(f"{context.city}/processed/{network}", calculator.gdf)
	pass


@then("join {series} within {radii_str} meters from {data_frame} to parcel layer via street network")
def step_impl(context, series, radii_str, data_frame):
	parcel_gdf = get_parcel_gdf(context.city)
	nodes_gdf = read_feather(f"{context.city}/network/street_node")
	links_gdf = read_feather(f"{context.city}/network/street_link")
	target_gdf = context.gdf_db[data_frame]
	radii = radii_str.split(", ")
	for radius in radii:
		analyst = SpatialAnalyst(parcel_gdf, target_gdf)
		network = Network(nodes_gdf, links_gdf)
		parcel_gdf_joined = SpatialNetworkAnalyst(analyst, network)\
			.buffer_join_network(int(radius))
		save_feather(f"{context.city}/parcel", parcel_gdf_joined)
	pass
