import os.path
import shutil

from behave import *
from pandas.api import types

from learnkit.train.Predictor import *
from utils.datautils import *
from utils.exportutils import *
from utils.gdfutils import *


@given("a dataset of georeferenced {parcel} geometries within the {city}")
def step_impl(state, parcel, city):
	state.city = city
	state.data = parcel
	state.parcel_samples = f"data/{city}/processed/samples/{parcel}.feather"
	state.predictors = f'data/{state.city}/processed/predictors'
	state.dependencies = f'data/{state.city}/processed/dependencies'
	state.importance = f'data/{state.city}/processed/importance'
	state.maps = f'data/{state.city}/processed/maps'
	state.test = f'data/{state.city}/processed/test'
	assert (os.path.exists(state.parcel_samples))
	pass


@when("the dataset includes valid quantitative and georeferenced data")
def step_impl(state, ):
	gdf = read_gdf(state.parcel_samples)
	assert (gdf.crs is not None)
	assert ('geometry' in gdf.columns)


@then("use {train_size}% of the available data to train a random forest model to predict {dependent} variable")
def step_impl(state, train_size, dependent):
	train_share = int(train_size)/100
	test_share = round(1 - train_share, 2)
	gdf = gpd.read_feather(state.parcel_samples)
	save_path = state.predictors

	assert (dependent in list(gdf.columns)), f"Could not find {dependent} within {list(gdf.columns)}."
	assert (types.is_numeric_dtype(gdf[dependent]))

	plot_choropleth_map(gdf, dependent, state.maps)

	not_explanatory = ["walk_r", "price_r", "walkability_r", "rent_price_r"]
	invalid_list = [col for col in gdf.columns for invalid in not_explanatory if invalid in col]
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
	predictor.save(save_path)
	assert (len(os.listdir(save_path)) > 0)


@step("a predictive model trained")
def step_impl(state):
	assert (len(os.listdir(state.predictors)) > 0)
	if not hasattr(state, "trained"):
		state.trained = {}
	for model in os.listdir(state.predictors):
		if ".pkl" not in model:
			continue
		state.trained[model] = load_pickle(f"{state.predictors}/{model}")
		pass


@then("assess predictive accuracy based on the test data")
def step_impl(state):
	directory = state.test
	check_and_clean_path(directory)
	for model in state.trained.keys():
		state.trained[model].test(plot_dir=directory)
	assert (len(os.listdir(directory)) > 0)


@step("rank explanatory variables by permutation importance")
def step_impl(state):
	directory = state.importance
	predictors = read_predictors(state.predictors)
	check_and_clean_path(directory)
	for predictor in predictors:
		df = predictor.get_permutation_importance()
		df.to_csv(f"{directory}/{predictor.predicted}.csv")
	assert (len(os.listdir(directory)) > 0)


@step("plot charts and maps of {count} most important variables")
def step_impl(state, count):
	gdf = read_samples(state.parcel_samples)
	features = read_important_features(state.importance, count)
	predictors = read_predictors(state.predictors)
	assert (len(features) == len(predictors))

	for i, feature_set in enumerate(features):
		[plot_choropleth_map(gdf, feature, state.maps) for feature in feature_set ]
		predictors[i].plot_partial_dependence(state.dependencies, feature_set)
	assert (len(os.listdir(state.maps)) > 0)
	assert (len(os.listdir(state.dependencies)) > 0)


@step("copy outputs to manuscript path")
def step_impl(state):
	folder_name = "processed"
	processed_directory = f"data/{state.city}/{folder_name}"
	manuscript_directory = f"{get_assets_directory()}/images"
	training_directory = f"{manuscript_directory}/training"
	if os.path.exists(training_directory):
		shutil.rmtree(training_directory)
	assert (os.path.exists(processed_directory))
	assert (os.path.exists(manuscript_directory))
	shutil.copytree(processed_directory, training_directory)
	cucumber_to_markdown("features/spatial_metrics.feature", f"{get_assets_directory()}/tables")


def read_samples(samples_path):
	return gpd.read_feather(samples_path)


def read_predictors(predictors_dir):
	return [load_pickle(f"{predictors_dir}/{model}") for model in os.listdir(predictors_dir) if ".pkl" in model]


def read_important_features(importance_dir, feature_count):
	features_nested_list = []
	for file in os.listdir(importance_dir):
		if ".csv" not in file:
			continue
		features_nested_list.append(list(
			pd.read_csv(f"{importance_dir}/{file}", encoding="latin1")
			.groupby('feature', as_index=False).sum()
			.sort_values('dependencies', ascending=False)
			.head(int(feature_count)).feature
		))
	return features_nested_list
