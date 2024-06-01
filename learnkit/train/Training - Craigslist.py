from Analyzer import *
from Variables import *
from Training import train_random_forest_regression


CGL_GDF = gpd.read_file(GPK, layer='craigslist_rent')

aff = NetworkAnalyst(CGL_GDF, OLD_NETWORK)
aff.gdf = aff.aggregate_spatial_indicators(directory=f'{DIRECTORY}/{CITY}', layers=LAYERS, radii=RADII)
aff.gdf = aff.get_distance_to_cbd(CBD_GDF)
aff.gdf.to_feather(f'{DIRECTORY}/{CITY}/craigslist_rent.feather')

# Define variables
GDF = gpd.read_feather(f'{DIRECTORY}/{CITY}/craigslist_rent.feather')
DROP = ['price_bed_mean', 'ACTUAL_LAND', 'index_cl', 'id', 'ACTUAL_TOTAL', 'price', 'node', 'index',
                  'description', 'date', 'descriptio', 'path', 'layer', 'bedrooms', 'geometry']
GDF = GDF.loc[:, [col for col in GDF if col not in DROP]]

dependents = ['price_bed', 'price_sqft']
train_random_forest_regression(GDF, random_state=0, dependents=dependents, explanatory=list(set(GDF.columns).difference(set(dependents))))
