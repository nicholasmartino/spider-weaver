from Analyzer import *
from Variables import *
from Training import train_random_forest_regression
import geopandas as gpd
from pandas.api.types import is_numeric_dtype
from shapeutils.ShapeTools import SpatialAnalyst
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import pickle

# Aggregate indicators
aff = NetworkAnalyst(BCA_GDF, OLD_NETWORK)
aff.gdf = gpd.read_feather(f'{DIRECTORY}/{CITY}/land_assessment_fabric_spatial_indicators.feather')
aff.gdf = aff.aggregate_spatial_indicators(directory=f'{DIRECTORY}/{CITY}', layers=LAYERS, radii=RADII)
aff.gdf = aff.get_distance_to_cbd(BCA_GDF)
aff.gdf.to_feather(f'{DIRECTORY}/{CITY}/land_assessment_fabric_spatial_indicators.feather')
aff.gdf = SpatialAnalyst(aff.gdf, zoning_gdf.loc[:, ['geometry', 'max_fsr']]).spatial_join()

predictors = [
    'age_r800_ave_flat', 'd2cbd', 'Population, 2016_r1600_ave_flat', 'SFA_r800_sum_flat', 'SFD_r800_sum_flat',
    'bicycle_parking_r1600_sum_flat', 'Population density per square kilometre, 2016_r800_ave_flat', 'age',
    'bike_straight_r1600_sum_flat', 'elevation_r1600_ave_flat', 'NUMBER_OF_BEDROOMS_r800_sum_flat',
    'bench_r1600_ave_flat', 'walk_straight_r1600_ave_flat', 'bank_r1600_ave_flat', 'lat', 'long', 'area'
]
# Predict land price
GDF = gpd.read_feather(f'{DIRECTORY}/{CITY}/land_assessment_fabric_spatial_indicators.feather')
GDF['area'] = GDF.area
GDF['lat'] = GDF.to_crs(4326).centroid.y
GDF['long'] = GDF.to_crs(4326).centroid.x

train_random_forest_regression(
GDF.loc[:, ['ACTUAL_LAND', 'ACTUAL_TOTAL'] + predictors], ['ACTUAL_LAND', 'ACTUAL_TOTAL'], predictors)

# Predict land price per square meter
predictors = [col for col in GDF.columns if is_numeric_dtype(GDF[col]) and (col not in ['ACTUAL_LAND', 'ACTUAL_TOTAL', 'land_value_sqm', 'node'])]
GDF['land_value_sqm'] = GDF['ACTUAL_LAND']/GDF['area']
train_random_forest_regression(
    GDF.loc[:, ['land_value_sqm'] + predictors], ['land_value_sqm'], predictors, random_state=1)

# Predict number of bedrooms
train_random_forest_regression(GDF.loc[:, ['NUMBER_OF_BEDROOMS'] + predictors], ['NUMBER_OF_BEDROOMS'], predictors)
