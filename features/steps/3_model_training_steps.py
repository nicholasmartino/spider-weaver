import os.path
import shutil
from typing import List, TypedDict

import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from behave import *
from geopandas import GeoDataFrame
from google.cloud import storage
from google.cloud.storage import Blob
from pandas.api import types

from features.utils.datautils import *
from features.utils.exportutils import *
from features.utils.gdfutils import *
from learnkit.train.Predictor import *


class Paths(TypedDict):
    city: str
    housing_rent: str
    waters_file: str
    street_file: str
    predictors: str
    dependencies: str
    importance: str
    maps: str
    test: str


def copy_gcs_path(bucket_name: str) -> bool:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # Create a local directory with the bucket name
    local_dir = f"data/{bucket_name}"
    os.makedirs(local_dir, exist_ok=True)
    
    # Download all blobs (files) from the bucket
    blobs: List[Blob] = list(bucket.list_blobs())
    for blob in blobs:
        if blob.name is None:
            continue
        
        # Create the full local path
        local_path: str = os.path.join(local_dir, blob.name)
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Download the file
        blob.download_to_filename(local_path)
    
    return True


@given("a dataset of georeferenced geometries within {city}")
def step_impl(paths: Paths, city: str):
    BASE_PATH = "data"
    city_id = city.lower().replace(" ", "-")
    paths.city = city
    paths.housing_rent = f"{BASE_PATH}/{city_id}/craigslist/housing_rent.feather"
    paths.waters_file = f"{BASE_PATH}/{city_id}/open_street_map/water_bodies"
    paths.street_file = f"{BASE_PATH}/{city_id}/network/street_link"
    paths.predictors = f"{BASE_PATH}/{city_id}/spider_weaver/predictors"
    paths.dependencies = f"{BASE_PATH}/{city_id}/spider_weaver/dependencies"
    paths.importance = f"{BASE_PATH}/{city_id}/spider_weaver/importance"
    paths.maps = f"{BASE_PATH}/{city_id}/spider_weaver/maps"
    paths.test = f"{BASE_PATH}/{city_id}/spider_weaver/test"

    assert os.path.exists(paths.housing_rent)
    pass


@when("the dataset includes valid quantitative and georeferenced data")
def step_impl(state: Paths) -> None:
    gdf: GeoDataFrame = read_gdf(state.housing_rent)  # type: ignore
    assert gdf.crs is not None
    assert "geometry" in gdf.columns


@then(
    "use {train_size}% of the available data to train a random forest model to predict {dependent} variable"
)
def step_impl(state: Paths, train_size: str, dependent: str) -> None:
    train_share = int(train_size) / 100
    test_share = round(1 - train_share, 2)
    gdf = gpd.read_feather(state.housing_rent)
    save_path = str(state.predictors)

    assert dependent in list(
        gdf.columns
    ), f"Could not find {dependent} within {list(gdf.columns)}."
    assert types.is_numeric_dtype(gdf[dependent])

    plot_choropleth_map(gdf, dependent, state.maps)

    not_explanatory: List[str] = ["walk_r", "price_r", "walkability_r", "rent_price_r"]
    invalid_list: List[str] = [
        col for col in gdf.columns for invalid in not_explanatory if invalid in col
    ]
    invalid_set: List[str] = ["geometry"] + list(set(invalid_list))
    explanatory: List[str] = list(set.difference(set(gdf.columns), invalid_set))

    predictor = Predictor(
        data=gdf,
        predictors=explanatory,
        predicted=dependent,
        percentile=98,
        test_size=test_share,
    )
    predictor.split()
    predictor.regressor = predictor.train()
    predictor.save(save_path)
    assert len(os.listdir(save_path)) > 0


@step("a predictive model trained")
def step_impl(state: Paths) -> None:
    assert len(os.listdir(state.predictors)) > 0
    if not hasattr(state, "trained"):
        state.trained = {}
    
    models: List[str] = list(os.listdir(state.predictors))
    for model in models:
        if ".pkl" not in model:
            continue
        state.trained[model] = load_pickle(f"{state.predictors}/{model}")
        pass

@then("assess predictive accuracy based on the test data")
def step_impl(state: Paths) -> None:
    directory = str(state.test)
    check_and_clean_path(directory)
    models: List[str] = list(state.trained.keys())
    for model in models:
        state.trained[model].test(plot_dir=directory)
    assert len(os.listdir(directory)) > 0


@step("rank explanatory variables by permutation importance")
def step_impl(state: Paths) -> None:
    directory = str(state.importance)
    predictors = read_predictors(state.predictors)
    check_and_clean_path(directory)

    for predictor in predictors:
        df = predictor.get_permutation_importance()
        df.to_csv(f"{directory}/{predictor.predicted}.csv")
    assert len(os.listdir(directory)) > 0


@step("plot maps of {count} most important variables")
def step_impl(state: Paths, count: int):
    gdf = read_samples(state.housing_rent)
    gdf2 = pd.concat(
        [read_feather(state.street_file), read_feather(state.waters_file).to_crs(26910)]
    )
    features: List[List[str]] = read_important_features(state.importance, count)
    predictors: List[Predictor] = read_predictors(state.predictors)
    assert len(features) == len(predictors)

    for feature_set in features:
        predicted: List[str] = [str(p.predicted) for p in predictors]
        [
            plot_choropleth_map(gdf, feature, state.maps, gdf2)
            for feature in feature_set + predicted
        ]
        gc.collect()
    assert len(os.listdir(state.maps)) > 0


@step("plot significance charts of {count} most important variables")
def step_impl(state: Paths, count: int) -> None:
    features = read_important_features(state.importance, count)
    predictors = read_predictors(state.predictors)
    assert len(features) == len(predictors)

    for i, feature_set in enumerate(features):
        predictors[i].plot_partial_dependence(state.dependencies, feature_set)
    assert len(os.listdir(state.dependencies)) > 0


@step("plot a correlation matrix of {count} most important features")
def step_impl(state: Paths, count: int) -> None:
    directory = str(state.dependencies)
    gdf: GeoDataFrame = gpd.read_feather(state.housing_rent)

    predictors: List[Predictor] = read_predictors(state.predictors)
    predicted: List[str] = [str(p.predicted) for p in predictors]

    features = read_important_features(state.importance, count)
    feature_set = list(
        set([feature for features in features for feature in features] + predicted)
    )
    assert len(feature_set) > 0
    for feature in feature_set:
        assert feature in gdf.columns

    corr = gdf.loc[:, feature_set].corr()
    file_path = f"{directory}/correlation_matrix.png"

    plt.figure(figsize=(12, 10))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu", cbar=True, square=True)
    plt.xticks(rotation=90, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(file_path, dpi=150, transparent=True)
    plt.close()
    assert os.path.exists(file_path)


@step("copy outputs to manuscript path")
def step_impl(state: Paths) -> None:
    folder_name = "spider_weaver"
    processed_directory = f"data/{state.city}/{folder_name}"
    manuscript_directory = f"{get_assets_directory()}/images"
    training_directory = f"{manuscript_directory}/training"

    if os.path.exists(training_directory):
        shutil.rmtree(training_directory)

    assert os.path.exists(processed_directory)
    assert os.path.exists(manuscript_directory)
    shutil.copytree(processed_directory, training_directory)
    cucumber_to_markdown(
        "features/spatial_metrics.feature", f"{get_assets_directory()}/tables"
    )


def read_samples(samples_path: str) -> GeoDataFrame:
    return gpd.read_feather(samples_path)


def read_predictors(predictors_dir: str) -> List[Predictor]:
    return [
        load_pickle(f"{predictors_dir}/{model}")
        for model in os.listdir(predictors_dir)
        if ".pkl" in model
    ]


def read_important_features(importance_dir: str, feature_count: int) -> List[List[str]]:
    features_nested_list: List[List[str]] = []
    for file in os.listdir(importance_dir):
        if ".csv" not in file:
            continue
        features_nested_list.append(
            list(
                pd.read_csv(f"{importance_dir}/{file}", encoding="latin1")
                .groupby("feature", as_index=False)
                .sum()
                .sort_values("dependencies", ascending=False)
                .head(int(feature_count))
                .feature
            )
        )
    return features_nested_list
