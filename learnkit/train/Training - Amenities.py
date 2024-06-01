from PhD.Analyzer import *
from PhD.Variables import *
from PhD.Training import train_random_forest_classifier


DEPENDENT = ['cafe']
OSM_GDF = gpd.read_file(GPK, layer='land_osm_amenities')
OSM_GDF.loc[OSM_GDF['amenity'] == 'cafe', 'cafe'] = 1

aff = AffordabilityAnalyzer(OSM_GDF, OLD_NETWORK)
aff.gdf = aff.aggregate_spatial_indicators(f'{DIRECTORY}/{CITY}', LAYERS, RADII)
aff.gdf = aff.get_distance_to_cbd(CBD_GDF)
aff.gdf.to_feather(f'{DIRECTORY}/{CITY}/land_osm_amenities.feather')

# Define variables
GDF = gpd.layer_exists(f'{DIRECTORY}/{CITY}/land_osm_amenities.feather')
DROP = []
GDF = GDF.loc[:, [col for col in GDF if col not in DROP]]
train_random_forest_classifier(gdf=GDF, dependent=DEPENDENT,
    explanatory=[col for col in OSM_GDF.columns if col not in DEPENDENT + ['geometry']])
