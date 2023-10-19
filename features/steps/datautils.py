from shapeutils.GeoDataFrameUtils import *


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
	processed_parcels_gdf_path = f"{path}/processed/parcel"
	if os.path.exists(processed_parcels_gdf_path):
		return read_feather(processed_parcels_gdf_path)
	return read_feather(f"{path}/parcel")


def validate_geo_dataframe(context, data_frame):
	assert (context.gdf_db is not None)
	assert (context.gdf_db[data_frame] is not None)
	assert (context.gdf_db[data_frame].crs is not None)
	assert (True in list(context.gdf_db[data_frame].geometry.is_valid))
	return True
