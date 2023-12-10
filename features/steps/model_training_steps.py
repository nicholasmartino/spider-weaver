import os.path

from behave import *
from pandas.api import types
from learnkit.train.Predictor import *
from datautils import *


@given("a dataset of georeferenced {parcel} geometries within the {city}")
def step_impl(state, parcel, city):
	state.city = city
	state.data = parcel
	state.data_path = f"data/{city}/processed/{parcel}.feather"
	state.model_path = f'data/{state.city}/processed/models'
	assert (os.path.exists(state.data_path))
	pass


@when("the dataset includes valid quantitative and georeferenced data")
def step_impl(state, ):
	gdf = read_gdf(state.data_path)
	assert (gdf.crs is not None)
	assert ('geometry' in gdf.columns)


@then("use {train_size}% of the available data to train a random forest model to predict {dependent} variable")
def step_impl(state, train_size, dependent):
	train_share = int(train_size)/100
	test_share = round(1 - train_share, 2)
	raw_gdf = gpd.read_feather(state.data_path)
	feature_dict = read_feature_dict(f"{state.city}/processed/feature_dict.json")
	gdf = raw_gdf.rename(feature_dict)

	assert (dependent in list(gdf.columns)), f"Could not find {dependent} within {list(gdf.columns)}."
	assert (types.is_numeric_dtype(gdf[dependent]))

	forbidden = ["walk_r", "price_r"]
	invalid_list = [col for col in gdf.columns for invalid in forbidden if invalid in col]
	invalid_set = ['geometry'] + list(set(invalid_list))
	explanatory = list(set.difference(set(gdf.columns), invalid_set))

	predictor = Predictor(
		data=gdf,
		predictors=explanatory,
		predicted=dependent,
		percentile=98,
		test_size=test_share
	)
	predictor.split()
	predictor.regressor = predictor.train()
	predictor.save(state.model_path)
	assert (len(os.listdir(state.model_path)) > 0)


@step("a predictive model trained with a data split")
def step_impl(state):
	assert (len(os.listdir(state.model_path)) > 0)
	if not hasattr(state, "trained"):
		state.trained = {}
	for model in os.listdir(state.model_path):
		state.trained[model] = load_pickle(f"{state.model_path}/{model}")
		pass


@then("assess predictive accuracy based on the test data")
def step_impl(state):
	plot_path = f'data/{state.city}/processed/test'
	check_and_clean_path(plot_path)
	for model in state.trained.keys():
		state.trained[model].test(plot_dir=plot_path)
	assert (len(os.listdir(plot_path)) > 0)


@step("rank significant predictors using partial dependence analysis")
def step_impl(state):
	plot_path = f'data/{state.city}/processed/predictors'
	check_and_clean_path(plot_path)
	for model in state.trained.keys():
		state.trained[model].plot_partial_dependence(plot_dir=plot_path)
	assert (len(os.listdir(plot_path)) > 0)
