import copy

from PhD.Generator import UrbanDesignGenerator
from PhD.Variables import *

sys.path.insert(1, f"{PYTHON_DIR}/city")
from Fabric import Neighbourhood, Parcels, Buildings


def get_coordinates(gdf):
    return [(pt.xy[0][0], pt.xy[1][0]) for pt in gdf.to_crs(4326).geometry]


cores_gdf = gpd.read_file('data/density_cores.geojson')
CENTERS = {
        'mono': [(-123.118119, 49.282532)],
        'base': get_coordinates(cores_gdf[cores_gdf['type'] == 'baseline']),
        'tod': get_coordinates(cores_gdf[cores_gdf['type'] == 'transit']),
        'art': get_coordinates(cores_gdf[cores_gdf['type'] == 'arterial'])
    }


def predict_indicators(gen):
    gen.extract_all_data()
    gen.neigh = gen.predict_rent_prices()
    gen.neigh = gen.predict_land_prices()
    gen.neigh.dump_pkl()
    gen.neigh.export('ESRI Shapefile', 4326, f'-{gen.prefix}predicted')
    return gen


def update_centers(gen):
    gen.neigh.parcels.gdf['land_value_sqm'] = gen.neigh.parcels.gdf['ACTUAL_LAND'] / gen.neigh.parcels.gdf.area
    for type_name, centers in CENTERS.items():
        gen.prefix = f"{type_name}-"
        gen.reset_centers(new_centers=centers)
        gen.neigh.parcels.gdf[f'{gen.prefix}_fsr'] = gen.neigh.parcels.gdf['fsr_rad']
    return gen


def filter_feasible_parcels(gen):
    baseline_neigh = copy.deepcopy(gen.neigh)
    for type_name, centers in CENTERS.items():
        gen.neigh.parcels.gdf['fsr'] = gen.neigh.parcels.gdf[f'{type_name}-_fsr']
        gen.filter_feasible_parcels()
        gen.neigh = copy.deepcopy(baseline_neigh)
        gen.neigh.export('GeoJSON', 26910, f'-{gen.prefix}feasibility')
    return gen


if __name__ == '__main__':
    streets_gdf = gpd.read_file('../data/public-streets.geojson')
    parcels_gdf = gpd.read_file(f'{OUT_DIR}/data/feather/parcels.geojson')
    # parcels_gdf.loc[:, [
    #     'land_value_sqm',
    #     'fsr_rad',
    #     'n_units',
    #     'mono-_fsr',
    #     'base-_fsr',
    #     'tod-_fsr',
    #     'art-_fsr',
    #     'geometry'
    # ]].to_crs(4326).to_file(f'{OUT_DIR}/data/geojson/parcels4326.geojson', driver='GeoJSON')
    GEN = UrbanDesignGenerator(
        neigh_centers=[],
        fsr_range=RANGES['fsr'],
        type_info=TYPE_INFO,
        unit_mix=UNIT_MIX,
        neighbourhood=Neighbourhood(
            name='Metro Vancouver Regional District',
            parcels=Parcels(gdf=parcels_gdf),
            # buildings=Buildings(gdf=BLD_FOOTPRINTS),
        )
    )

    # GEN = predict_indicators(GEN)
    # GEN = update_centers(GEN)
    GEN = filter_feasible_parcels(GEN)
