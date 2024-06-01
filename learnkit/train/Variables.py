import os
import sys
import time

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(1, f"/morphology")
from NetworkTools import Network

pd.options.display.max_columns = 10
pd.set_option('display.width', 1000)

start_time = time.time()

CITY = 'Metro Metro Vancouver Regional District, British Columbia'

if 'win32' in sys.platform:
    DIRECTORY = f'G:/My Drive/Python/morphology'
    ELABS_DATA = 'G:/My Drive/UBC/elementslab/Data'
    PYTHON_DIR = f'G:/My Drive/Python'
    OUT_DIR = f'{PYTHON_DIR}/morphology/PhD'
else:
    DIRECTORY = f'/Volumes/Samsung_T5/Python/morphology'
    ELABS_DATA = '/Volumes/GoogleDrive/My Drive/UBC/elementslab/Data'
    PYTHON_DIR = '/Volumes/GoogleDrive/My Drive/Python'
    OUT_DIR = f'{DIRECTORY}/PhD'

MODEL_DIR = f'{PYTHON_DIR}/morphology/PhD/models'
GPK = f'{DIRECTORY}/{CITY}.gpkg'

DPI = 300
R_SEEDS = 30
CRS = 26910
MAX_BLOCK = 2400
MIN_PARCEL = 1000
RADII = [1600, 800]

RANGES = {
    'fsr': np.arange(0.25, 10, 0.25),
    'building_depth': range(9, 15),
    'building_height': range(6, 150),
    'parcel_width': range(12, 60),
    'street_width': range(16, 16)
}

UNIT_MIX = [
    # https://www.statista.com/statistics/651099/average-price-per-square-meter-of-an-apartment-in-vancouver/
    {'type': '2 Bedroom', 'share': 0.3, 'area': 120, 'price': 6957},
    # $/m2 # Model a RNN to predict house price/m2 based on population/dwelling density from census dissemination data
    {'type': '1 Bedroom', 'share': 0.5, 'area': 75, 'price': 5232},
    {'type': 'Studio', 'share': 0.2, 'area': 50, 'price': 5636}
]

TYPE_INFO = {
    'Type': ['Townhouse', 'Low-Mid-Rise', 'High-Rise'],
    # 'Cost': [(1730, 2270), (2360, 3800), (3240, 3730)], # https://www.statista.com/statistics/972884/-building-costs-bc-canada-by-type/
    'Cost': [(2250, 2250), (2400, 2400), (3200, 3200)],
    'Height': [6, 21, max(RANGES['building_height'])],
    'Occupancy': [0.6, 0.6, 0.6],
}

LAYERS = {
    'land_osm_amenities': ['amenity'],
    'network_stops': ["frequency"],
    'network_nodes': ["elevation"],
    'network_walk': ["walk_length", "walk_straight"],
    'network_bike': ["bike_length", "bike_straight"],
    'network_drive': ["drive_length", "drive_straight"],
    'land_assessment_fabric_cl': ["n_use", "age", "NUMBER_OF_BEDROOMS"],
    'land_assessment_parcels': ["area_sqkm"],
    'land_dissemination_area': ["Population, 2016", "Population density per square kilometre, 2016", "n_dwellings"],
}


full_run = 0

if full_run:
    OLD_NETWORK = Network(
        nodes_gdf=gpd.read_file(GPK, layer='network_nodes'),
        edges_gdf=gpd.read_file(GPK, layer='network_links')
    )
    OLD_PARCELS = gpd.read_feather(f'{OUT_DIR}/data/feather/parcel_bckp.feather').to_crs(CRS)  # !!!
    OLD_AMENITIES = gpd.read_file(GPK, layer='land_osm_amenities')
    OLD_AMENITIES = OLD_AMENITIES[OLD_AMENITIES['amenity'].isin([
        'bench',
        'restaurant',
        'bicycle_parking',
        'cafe',
        'fast_food',
        'waste_basket',
        'post_box',
        'toilets',
        'bank',
        'drinking_water',
        'parking',
        'parking_entrance',
        'bicycle_rental',
        'dentist',
        'fuel',
        'pub',
        'post_office',
        'bar',
        'public_bookcase',
        'clinic',
        'place_of_worship',
        'vending_machine',
        'car_sharing',
        'atm',
        'ice_cream',
        'recycling',
        'waste_disposal',
        'school',
        'charging_station',
        'veterinary'
    ])]
    BCA_GDF = gpd.read_feather(f'{DIRECTORY}/{CITY}/property.feather')
    CBD_GDF = gpd.read_file(GPK, layer='land_cbd')
    BLD_FOOTPRINTS = gpd.read_feather(f'{OUT_DIR}/data/feather/building_footprints.feather')

    if 'local_areas.feather' not in os.listdir('../data/CoV'):
        LOCAL_AREAS = gpd.read_file('https://opendata.vancouver.ca/explore/dataset/local-area-boundary/download/?format=geojson&timezone=America/Los_Angeles&lang=en').to_crs(CRS)
        LOCAL_AREAS.to_feather('../data/CoV/local_areas.feather')
    else:
        LOCAL_AREAS = gpd.read_feather('../data/CoV/local_areas.feather')

    if 'building_footprints.feather' not in os.listdir('../data/CoV'):
        BLD_FOOTPRINTS = gpd.read_file('https://opendata.vancouver.ca/explore/dataset/building-footprints-2009/download/?format=geojson&timezone=America/Los_Angeles&lang=en').to_crs(CRS)
        BLD_FOOTPRINTS.to_feather('../data/CoV/building_footprints.feather')
    else:
        BLD_FOOTPRINTS = gpd.read_feather('../data/CoV/building_footprints.feather')

    if 'parks.feather' not in os.listdir('../data/CoV'):
        PARKS = gpd.read_file('https://opendata.vancouver.ca/explore/dataset/parks-polygon-representation/download/?format=geojson&timezone=America/Los_Angeles&lang=en').to_crs(CRS)
        PARKS.to_feather('../data/CoV/parks.feather')
    else:
        PARKS = gpd.read_feather('../data/CoV/parks.feather')
    PARKS['geometry'] = PARKS.buffer(1)

RENAME_MASK = {
    'acc': 'Accessibility',
    'aff': 'Affordability',
    '1600': '1600m radius',
    '400': '400m radius',
    '4800': '4800m radius',
    '800': '800m radius',
    'aff_axial_degree': 'Axial degree centrality',
    'aff_axial_closeness': 'Axial closeness centrality',
    'aff_axial_closeness_r3200_ave_f': 'Average axial closeness within 3200m',
    'aff_axial_eigenvector': 'Axial eigenvector centrality',
    'aff_axial_katz': 'Axial katz centrality',
    'aff_axial_hits1': 'Axial hits centrality',
    'aff_axial_betweenness': 'Axial betweenness centrality',
    'aff_axial_length': 'Axial line length',
    'aff_axial_n_betweenness': 'Normalized axial betweenness centrality',
    'aff_connectivity': 'Axial connectivity',
    'aff_node_closeness': 'Street affersection closeness centrality',
    'aff_length': 'Street length',
    'aff_link_betweenness': 'Street segment betweenness centrality',
    'aff_link_n_betweenness': 'Normalized street segment betweenness',
    'aff_network_drive_ct': 'Number of streets',
    'aff_node_betweenness': 'Intersection betweenness',
    'f': 'No distance-decay function',
    'aff_area': 'Parcel area',
    'aff_area_r3200_ave_f': 'Average parcel area within 3200m',
    'aff_area_r4800_ave_f': 'Average parcel area within 4800m',
    'aff_ave_n_rooms': 'Number of rooms',
    'aff_ave_n_rooms_r400_f': 'Average number of rooms within 400m',
    'aff_cc_per': 'Tree canopy cover',
    'aff_cc_per_r4800_rng_f': 'Range of tree canopy cover within 4800m',
    'aff_gross_building_area': 'Gross building area',
    'aff_gross_building_area_r4800_sum_f': 'Total gross building area within 4800m',
    'aff_imp_per': 'Impervious surfaces',
    'aff_imp_per_r1600_sum_l': 'Impervious surfaces within 1600m',
    'aff_land_assessment_fabric_r1600_cnt_l': 'Number of parcels within 1600m',
    'aff_land_assessment_parcels': 'Number of parcels',
    'aff_land_assessment_parcels_ct': 'Number of parcels',
    'aff_n_dwellings': 'Number of dwellings',
    'aff_n_dwellings_r1600_sum_f': 'Number of dwellings within 1600m',
    'aff_number_of_bathrooms': 'Number of bathrooms',
    'aff_number_of_bedrooms': 'Number of bedrooms',
    'aff_number_of_storeys': 'Number of storeys',
    'aff_number_of_storeys_r4800_sum_f': 'Total number of storeys within 4800m',
    'aff_pcc_veg': 'Potential planting area',
    'aff_pcc_veg_r4800_ave_l': 'Average potential planting area within 4800m',
    'aff_total_bedr': 'Number of bedrooms',
    'aff_total_bedr_r400_ave_f': 'Average number of bedrooms within 400m',
    'aff_total_bedr_r1600_sum_f': 'Number of bedrooms within 1600m',
    'aff_total_finished_area': 'Total finished area',
    'aff_total_finished_area_r1600_ave_f': 'Average finished area within 1600m',
    'aff_year_built': 'Year built',
    'l': 'Linear distance-decay function',
    'aff_400 to 800': 'Small-sized parcels (400 - 800m2)',
    'aff_800 to 1600': 'Medium-sized parcels (800 - 1600m2)',
    'aff_building_age_div_sh': 'Building age diversity (Shannon)',
    'aff_building_age_div_sh_r400_ave_f': 'Average building age diversity (Shannon)',
    'aff_building_age_div_si': 'Building age diversity (Simpson)',
    'aff_dwelling_div_bedrooms_sh': 'Dwelling diversity (Shannon index, number of bedrooms)',
    'aff_dwelling_div_rooms_sh': 'Dwelling diversity (Shannon index, number of rooms)',
    'aff_dwelling_div_rooms_si': 'Dwelling diversity (Simpson index, number of rooms)',
    'aff_dwelling_div_rooms_si_r4800_rng_f': 'Dwelling diversity, number of rooms (Simpson) within 4800m',
    'aff_dwelling_div_rooms_si_r4800_rng_l': 'Dwelling diversity, number of rooms (Simpson) within 4800m',
    'aff_dwelling_div_bedrooms_si': 'Dwelling diversity (number of bedrooms)',
    'aff_n_size': 'Diversity of parcel size',
    'aff_n_size_r800_si_div_l': 'Diversity of parcel sizes within 800m',
    'aff_more than 6400': 'Large parcels (more than 6400m2)',
    'aff_node_closeness_r800_sum_f': 'Total affersection closeness within 800m',
    'aff_population density per square kilometer, 2016_r800_sum_f': 'Total population density within 800m',
    'aff_population density per square kilometer, 2016_r1600_sum_f': 'Total population density within 1600m',
    'aff_population density per square kilometer, 2016_r3200_sum_f': 'Average population density within 3200m',
    'aff_population density per square kilometer, 2016_r4800_sum_f': 'Total population density within 4800m',
    'aff_n_dwellings_r800_sum_f': 'Total number of dwellings within 800m',
    'aff_number_of_bathrooms_r4800_ave_f': 'Average number of bathrooms within 4800m'
}

print(f'> Variables read in {round((time.time() - start_time) / 60, 2)} minutes')
