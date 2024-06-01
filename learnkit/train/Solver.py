import copy
import pickle

from Generator import UrbanDesignGenerator
from PhD.Variables import *
import numpy as np
sys.path.insert(1, f"{PYTHON_DIR}/urban-zoning")
from City.Network import Streets
from City.Fabric import *

gen = UrbanDesignGenerator(neigh_centers=[], fsr_range=RANGES['fsr'], type_info=TYPE_INFO, unit_mix=UNIT_MIX,
    neighbourhood=Neighbourhood(
        name='Strathcona',
        # streets=Streets(gdf=gpd.read_file('../data/public-streets.geojson')),
        # parcels=Parcels(gdf=gpd.overlay(gpd.overlay(LOCAL_AREAS[LOCAL_AREAS['name'].isin(['Strathcona'])], OLD_PARCELS), PARKS.loc[:, ['geometry']], how='difference')),
        # buildings=Buildings(gdf=gpd.overlay(LOCAL_AREAS[LOCAL_AREAS['name'].isin(['Strathcona'])], BLD_FOOTPRINTS)),
        # boundary=LOCAL_AREAS[LOCAL_AREAS['name'].isin(['Strathcona'])]
))

# Predict
# gen.neigh.export('ESRI Shapefile', 4326, f'-{gen.prefix}baseline')
# gen.extract_local_data()
# gen.neigh = gen.predict_rent_prices()
# gen.neigh = gen.predict_land_prices()
# gen.neigh.dump_pkl()
gen.neigh = gen.neigh.load_pkl()
baseline_neigh = copy.deepcopy(gen.neigh)

for type_name, centers in {
    'mono': [(-123.096875, 49.277551)],
    # 'poly': [(pt.xy[0][0], pt.xy[1][0]) for pt in gpd.overlay(OLD_NETWORK.edges[OLD_NETWORK.edges['name'] == 'East Hastings Street'], LOCAL_AREAS[LOCAL_AREAS['name'].isin([gen.neigh.name])]).to_crs(4326).geometry],
    # 'dis': [(pt.xy[0][0], pt.xy[1][0]) for pt in gpd.overlay(OLD_NETWORK.nodes, LOCAL_AREAS[LOCAL_AREAS['name'].isin([gen.neigh.name])]).to_crs(4326).geometry]
}.items():
    gen.prefix = f"{type_name}-"
    gen.reset_centers(new_centers=centers)
    gen.add_all_centers()

    # Assess
    gen.neigh = gen.filter_feasible_parcels()
    gen.neigh = gen.assemble_and_subdivide(street_width=16)
    gen.neigh.export('ESRI Shapefile', 4326, f'-{gen.prefix}subdivision')

    # Build
    gen.neigh = gen.generate_new_urban_forms()
    # gen.neigh = gen.classify_amenities()
    # gen.neigh = gen.predict_all_indicators()
    gen.neigh.export('ESRI Shapefile', 4326, f'-{gen.prefix}design')

    # Reset baseline
    gen.neigh = baseline_neigh
    baseline_neigh = copy.deepcopy(gen.neigh)
