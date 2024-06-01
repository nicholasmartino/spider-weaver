import gc
import math
import pickle
import random

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import BayesianRidge, LinearRegression
from sklearn.ensemble import RandomForestRegressor, BaggingRegressor
from sklearn.isotonic import IsotonicRegression
from sklearn.svm import SVR
from tqdm import tqdm
from sklearn.preprocessing import MinMaxScaler
from PhD.Analyzer import AffordabilityAnalyzer
from PhD.Variables import *
from shapeutils.ShapeTools import SpatialAnalyst

sys.path.insert(1, PYTHON_DIR)
sys.path.insert(1, f"{PYTHON_DIR}/city")
sys.path.insert(1, f"{PYTHON_DIR}/geolearning")
sys.path.insert(1, f"D:{PYTHON_DIR}/morphology")
sys.path.insert(1, f"{PYTHON_DIR}/urban-zoning")

from shapeutils.ShapeTools import Shape

from city.Fabric import *
from city.Zoning import *

DEV_TYPES = {
    'Townhouse': ['Townhouse'],
    'Low-Mid-Rise': ['Podium', 'Detached'],
    'High-Rise': ['Podium', 'Cascading']
}
BLD_TYPES = {i: k for k, l in DEV_TYPES.items() for i in l}


def depth_from_coverage(gdf, court=True):
    assert 'max_coverage' in gdf.columns, KeyError("'coverage' column not found")
    assert 'geometry' in gdf.columns, KeyError("'geometry' column not found")

    for i in range(1, 100):
        if court: gdf[f'buffer_{i}'] = (gdf.area - gdf.buffer(-i).area)/gdf.area
        else: gdf[f'buffer_{i}'] = gdf.buffer(-i).area/gdf.area
    buffer_cols = [col for col in gdf.columns if 'buffer' in col]
    gdf.loc[:, buffer_cols] = gdf.loc[:, buffer_cols].replace(1.0, np.nan)
    gdf = gdf.dropna(axis=1)
    buffer_cols = [col for col in gdf.columns if 'buffer' in col]

    st = time.time()
    gdf['regressors'] = [LinearRegression() for i in gdf.index]
    gdf['fitted'] = [gdf.loc[i, 'regressors'].fit(
        X=gdf.loc[[i], buffer_cols].T, y=[-int(col.split('buffer_')[1]) for col in buffer_cols]) for i in gdf.index]
    gdf['court_depth'] = [gdf.loc[i, 'regressors'].predict([[gdf.loc[i , 'max_coverage']]])[0] for i in gdf.index]
    print(f"Depth calculated with comprehensive list ({int(time.time() - st)}s)")

    # st = time.time()
    # for i in list(gdf.index):
    #     if len(gdf.loc[:, buffer_cols].T) > 0:
    #         rfr = RandomForestRegressor()
    #         rfr.fit(X=gdf.loc[[i], buffer_cols].T, y=[-int(col.split('buffer_')[1]) for col in buffer_cols])
    #         gdf.loc[i, 'depth'] = rfr.predict([[gdf.loc[i , 'max_coverage']]])
    #         # gdf = gdf.drop(buffer_cols, axis=1)
    #     else:
    #         gdf.loc[i, 'depth'] = 0
    # print(f"Depth calculated with traditional for loop ({time.time() - st}s)")

    return gdf


def height_from_fsr(gdf, coverage=0.6):
    assert 'fsr' in gdf.columns, KeyError("'fsr' column not found")
    assert sum(gdf.area), KeyError("Empty gdf, height from fsr not extracted")
    max_floor_area = coverage * gdf.area
    max_built_area = gdf['fsr'] * gdf.area
    gdf['height'] = max_built_area / max_floor_area
    return gdf


def plot_multiple(gdf, filepath):
    """
    Plot each column in a separate axis and save the file

    :param gdf:
    :param filepath:
    :return:
    """
    assert 'geometry' in gdf.columns, AssertionError("Geometry column not found")

    vmin = min(gdf.min())
    vmax = max(gdf.max())
    fig, axs = plt.subplots(2, len(gdf.columns) - 1, figsize=(12, 3 * (len(gdf.columns) - 1)))
    non_geom_cols = [col for col in gdf.columns if col != 'geometry']
    for i, col in enumerate(non_geom_cols):
        axis = axs[0][i]
        gdf.plot(col, ax=axis, vmin=vmin, vmax=vmax, cmap='rainbow').set_axis_off()
        axis.set_title(col)
        gdf[col].plot(kind='hist', ax=axs[1][i], range=(vmin, vmax), cmap='rainbow')
    fig.savefig(filepath, dpi=100, transparent=True)
    return


class UrbanDesignGenerator:
    def __init__(self, neigh_centers, fsr_range, type_info, unit_mix, neighbourhood=None, network=None, amenities=None, bca=None, prefix=''):
        self.neigh = neighbourhood
        self.neigh_centers = neigh_centers
        self.fsr_range = fsr_range

        self.type_info = type_info
        self.unit_mix = unit_mix

        self.network = network
        self.amenities = amenities
        self.bca = bca
        self.aff_an = None
        self.prefix = prefix
        return

    def add_all_centers(self):
        for center in self.neigh_centers:
            self.neigh.add_center(center)
        self.neigh.assign_gradient_fsr(self.fsr_range, max_dist=600)  # !!!
        return

    def reset_centers(self, new_centers):
        self.neigh.centers = gpd.GeoDataFrame({'geometry': []}, geometry='geometry', crs=4326)
        self.neigh_centers = new_centers
        self.add_all_centers()
        return

    def estimate_built_area(self):
        parcels = self.neigh.parcels.gdf.copy()
        buildings = self.neigh.buildings.gdf.copy()
        buildings['gfa'] = (buildings['height']/3) * buildings.area
        parcels = SpatialAnalyst(parcels, buildings.loc[:, ['gfa', 'geometry']]).spatial_join(operations=['sum'])
        return parcels

    def extract_local_data(self):
        gdf = self.neigh.parcels.gdf.copy()
        gdf = gdf[gdf['geometry'].isna()]
        bounds = gpd.GeoDataFrame({'geometry': [gdf.unary_union.buffer(max(RADII))]}, crs=gdf.crs)  # Maybe a method of Neighbourhood object?
        self.network = Network(
            nodes_gdf=gpd.overlay(OLD_NETWORK.nodes, bounds), edges_gdf=gpd.overlay(OLD_NETWORK.edges, bounds))
        self.amenities = gpd.overlay(OLD_AMENITIES, bounds)
        self.bca = gpd.overlay(BCA_GDF, bounds)
        self.neigh.parcels.gdf = self.estimate_built_area()
        return

    def extract_all_data(self):
        self.network = Network(
            nodes_gdf=OLD_NETWORK.nodes, edges_gdf=OLD_NETWORK.edges)
        self.amenities = OLD_AMENITIES
        self.bca = BCA_GDF
        self.neigh.parcels.gdf = self.estimate_built_area()
        return

    def join_bca_data(self):
        neigh = self.neigh
        aff = AffordabilityAnalyzer(neigh.parcels.gdf, self.network)
        neigh.parcels.gdf = aff.join_bc_assessment_data(self.bca)
        return neigh

    def aggregate_spatial_indicators(self):
        if self.aff_an is None:
            aff = AffordabilityAnalyzer(self.neigh.parcels.gdf, self.network)

            # Aggregate spatial indicators
            aff.gdf = aff.aggregate_spatial_indicators(f'{DIRECTORY}/{CITY}', LAYERS, RADII)
            aff.gdf = aff.get_distance_to_cbd(CBD_GDF)
            self.aff_an = aff

    def predict_rent_prices(self):
        neigh = self.neigh
        self.aggregate_spatial_indicators()
        neigh.parcels.gdf = self.aff_an.predict_indicator(model_dir=MODEL_DIR, indicators=['price_bed', 'price_sqft'])
        return neigh

    def predict_land_prices(self):
        neigh = self.neigh
        self.aggregate_spatial_indicators()
        neigh.parcels.gdf['lat'] = neigh.parcels.gdf.to_crs(4326).centroid.y
        neigh.parcels.gdf['long'] = neigh.parcels.gdf.to_crs(4326).centroid.x
        # neigh.parcels.gdf = self.aff_an.predict_indicator(model_dir=MODEL_DIR, indicators=['ACTUAL_LAND', 'ACTUAL_TOTAL'])
        neigh.parcels.gdf = self.aff_an.predict_indicator(model_dir=MODEL_DIR, indicators=['land_value_sqm'])
        return neigh

    def predict_number_of_bedrooms(self):
        parcels_gdf = self.neigh.parcels.gdf.copy().to_crs(26910)
        rfr = pickle.load(open(f"{MODEL_DIR}/predictor-NUMBER_OF_BEDROOMS.pkl", 'rb'))
        # orig_train_data = pickle.load(open(f'{MODEL_DIR}/NUMBER_OF_BEDROOMS_TrainData.sav', 'rb'))['NUMBER_OF_BEDROOMS']
        # valid_gdf = parcels_gdf.loc[:, orig_train_data.columns].dropna()
        parcels_gdf.dropna().loc[:, 'NUMBER_OF_BEDROOMS'] = rfr.predict(parcels_gdf)

        # reg = Regression(directory=MODEL_DIR, predicted=['NUMBER_OF_BEDROOMS'], plot=False)
        #
        # assert f'NUMBER_OF_BEDROOMS_TrainData{reg.suffix}.sav' in os.listdir(MODEL_DIR), AssertionError(
        #     f'NUMBER_OF_BEDROOMS_TrainData.sav not in {MODEL_DIR}')
        # assert f'NUMBER_OF_BEDROOMS_FittedModel.sav' in os.listdir(MODEL_DIR), AssertionError(
        #     f'NUMBER_OF_BEDROOMS_FittedModel.sav not in {MODEL_DIR}')
        #
        # # Predict residential rent prices
        #
        # for col in orig_train_data:
        #     assert col in parcels_gdf.columns, AssertionError(f"{col} not found in analyzer's GeoDataFrame")
        #
        # reg.train_data = {'NUMBER_OF_BEDROOMS': parcels_gdf.loc[:, orig_train_data.columns].dropna()}
        # reg.fitted = pickle.load(open(f'{MODEL_DIR}/NUMBER_OF_BEDROOMS_FittedModel.sav', 'rb'))
        # reg.r_seed = pickle.load(open(f'{MODEL_DIR}/NUMBER_OF_BEDROOMS_RandomState.sav', 'rb'))
        # reg.method = pickle.load(open(f'{MODEL_DIR}/NUMBER_OF_BEDROOMS_Method.sav', 'rb'))
        # predicted = reg.pre_norm_exp(parcels_gdf.loc[:, orig_train_data.columns].dropna())
        # parcels_gdf.loc[predicted.index, 'NUMBER_OF_BEDROOMS'] = predicted.loc[:, 'NUMBER_OF_BEDROOMS_rf']
        print(f"Average number of bedrooms predicted: {round(parcels_gdf['NUMBER_OF_BEDROOMS'].mean(), 2)}")
        return parcels_gdf

    def filter_feasible_parcels(self, min_area=100, max_area=10000, max_density=0.3):
        """
        Filter neighbourhood parcels and assess development types based on financial feasibiity

        :param min_area: Minimum parcel area
        :param max_area: Maximum parcel area
        :param max_density: Maximum unit density
        :return:
        """
        start_time = time.time()

        # parcels_gdf = self.predict_number_of_bedrooms()
        parcels_gdf = self.neigh.parcels.gdf.copy()
        out_cols = [
            'geometry'
            'area',
            'n_units',
            'units_per_sqm',
            'rent_bed',
            'rent_area',
            'land_value',
            'land_value_sqm',
            'dem_cost',
            'fsr',
            'height',
            'largest_residual',
            'feasible',
            'type'
        ]

        # Filter weird data
        parcels_gdf['units_per_sqm'] = parcels_gdf['n_units']/parcels_gdf['area']
        parcels_gdf = parcels_gdf[
            (parcels_gdf['area'] > min_area) &
            (parcels_gdf['area'] <= max_area) &
            (parcels_gdf['units_per_sqm'] < max_density)
        ]

        parcels_gdf['rent_bed'] = (parcels_gdf['NUMBER_OF_BEDROOMS'] * parcels_gdf['price_bed']).fillna(0)
        parcels_gdf['rent_area'] = (parcels_gdf['GROSS_BUILDING_AREA'] * parcels_gdf['price_sqft'])
        parcels_gdf['land_value'] = parcels_gdf['land_value_sqm'] * parcels_gdf['area']

        # Estimate demolition costs (https://askinglot.com/how-much-does-it-cost-to-tear-down-a-building &
        # https://www.phaseonedesign.ca/post/cost-tear-rebuild-home-vancouver)
        parcels_gdf['dem_cost'] = (parcels_gdf['gfa_sum'] * 10) + 15000  # Demolition cost per sqm + Demolition permit

        parcels_gdf['fsr'] = parcels_gdf['fsr_rad']
        # parcels_gdf.plot(column='fsr', legend=True, figsize=(16, 16)).set_axis_off()
        # plt.savefig(f'figures/{self.prefix}floor_space_ratio.png', dpi=100, transparent=True)

        parcels_gdf = height_from_fsr(parcels_gdf)

        scaler = MinMaxScaler(RANGES['building_height'])
        parcels_gdf['height'] = scaler.fit_transform(parcels_gdf['fsr'].values.reshape(-1, 1))

        dev = Development(
            parcel=parcels_gdf,
            fsr=parcels_gdf['fsr'],
            rent=parcels_gdf['price_bed'],
            units=pd.DataFrame(UNIT_MIX),
            current_units=parcels_gdf['n_units'],
            dem_cost=parcels_gdf['dem_cost'],
            max_height=parcels_gdf['height']
        )

        random.seed(2)
        for j, tp in enumerate(TYPE_INFO['Type']):
            dev.hard_costs = random.choice(TYPE_INFO['Cost'][j])
            dev.site_cover = TYPE_INFO['Occupancy'][j]
            parcels_gdf[f'height_{tp}'] = TYPE_INFO['Height'][j]
            dev.max_height = parcels_gdf.loc[:, ['height', f'height_{tp}']].min(axis=1)
            parcels_gdf[f'practical_fsr_{tp}'] = dev.practical_fsr()
            parcels_gdf[f'value_redev_{tp}'] = dev.value_redevelop()
            parcels_gdf[f'value_income_{tp}'] = dev.value_rent()
            parcels_gdf[f'residual_land_{tp}'] = dev.value_land_residual()
            parcels_gdf[f'residual_sqm_{tp}'] = parcels_gdf[f'residual_land_{tp}'] / parcels_gdf[f'area']
            parcels_gdf[f'net_revenue_{tp}'] = parcels_gdf[f'net_revenue']
            parcels_gdf[f'gross_revenue_{tp}'] = parcels_gdf[f'gross_revenue']
            parcels_gdf[f'total_costs_{tp}'] = parcels_gdf[f'total_costs']
            parcels_gdf[f'subtotal_{tp}'] = parcels_gdf[f'subtotal']
            parcels_gdf[f'interim_fin_{tp}'] = parcels_gdf[f'interim_fin']
            parcels_gdf[f'total_{tp}'] = parcels_gdf[f'total']
            parcels_gdf[f'total_tax_{tp}'] = parcels_gdf[f'total_tax']
            parcels_gdf[f'profit_{tp}'] = parcels_gdf[f'profit']
            out_cols = out_cols + [
                f'height_{tp}',
                f'practical_fsr_{tp}',
                f'value_redev_{tp}',
                f'value_income_{tp}',
                f'gross_revenue_{tp}',
                f'net_revenue_{tp}',
                f'total_costs_{tp}',
                f'subtotal_{tp}',
                f'interim_fin_{tp}',
                f'total_{tp}',
                f'total_tax_{tp}',
                f'profit_{tp}',
                f'residual_land_{tp}',
                f'residual_sqm_{tp}'
            ]
        # # Get valuation of property by different metrics
        # for i in tqdm(parcels_gdf.index):
        #     random.seed(0)
        #     np.random.seed(0)
        #
        #     # Assess feasibility for multiple housing types and pick the most profitable ones
        #     # https://www.statista.com/statistics/972884/-building-costs-bc-canada-by-type/
        #     fsr = parcels_gdf.loc[i, 'fsr']
        #     dev = Development(parcel=parcels_gdf.loc[[i], :], fsr=fsr, rent=parcels_gdf.loc[i, 'rent_bed'],
        #                       units=pd.DataFrame(UNIT_MIX), current_units=parcels_gdf.loc[i, 'n_units'],
        #                       dem_cost=parcels_gdf.loc[i, 'dem_cost'])
        #
        #     for j, tp in enumerate(TYPE_INFO['Type']):
        #         random.seed(j)
        #         dev.fsr = fsr
        #         dev.hard_costs = random.choice(TYPE_INFO['Cost'][j])
        #         dev.max_height = min(TYPE_INFO['Height'][j], height_from_fsr(parcels_gdf.loc[[i], :]).loc[i, 'height'])
        #         dev.site_cover = TYPE_INFO['Occupancy'][j]
        #         parcels_gdf.loc[i, f'height_{tp}'] = dev.max_height
        #         parcels_gdf.loc[i, f'practical_fsr_{tp}'] = dev.practical_fsr()
        #         parcels_gdf.loc[i, f'value_redev_{tp}'] = dev.value_redevelop()
        #         parcels_gdf.loc[i, f'value_income_{tp}'] = dev.value_rent()
        #         parcels_gdf.loc[i, f'residual_land_{tp}'] = dev.value_land_residual()
        #         parcels_gdf.loc[i, f'residual_sqm_{tp}'] = parcels_gdf.loc[i, f'residual_land_{tp}']/parcels_gdf.loc[i, f'area']

        for tp in self.type_info['Type']:
            other_types = [t for t in self.type_info['Type'] if t != tp]
            parcels_gdf[f'residual_{tp}>value_income_{tp}'] = \
                parcels_gdf[f'residual_land_{tp}'] > parcels_gdf[f'value_income_{tp}']
            parcels_gdf[f'residual_{tp}>land_value'] = \
                parcels_gdf[f'residual_land_{tp}'] > parcels_gdf['land_value']
            parcels_gdf[f'feasible_{tp}'] = \
                parcels_gdf[f'residual_{tp}>land_value'] & parcels_gdf[f'residual_{tp}>value_income_{tp}']
            parcels_gdf[f'dev_type_{tp}'] = \
                parcels_gdf.loc[:, f'residual_land_{tp}'] \
                > parcels_gdf.loc[:, [f'residual_land_{t}' for t in other_types]].max(axis=1)
            out_cols = out_cols + [
                f'residual_{tp}>value_income_{tp}',
                f'residual_{tp}>land_value',
                f'feasible_{tp}',
                f'dev_type_{tp}'
            ]

        parcels_gdf['largest_residual'] = \
            parcels_gdf.loc[:, [f'residual_land_{tp}' for tp in self.type_info['Type']]].max(axis=1)
        parcels_gdf['feasible'] = \
            parcels_gdf.loc[:, [f'feasible_{tp}'for tp in self.type_info['Type']]].sum(axis=1) > 0

        for tp in self.type_info['Type']:
            parcels_gdf.loc[(parcels_gdf[f'dev_type_{tp}'] & parcels_gdf['feasible']), 'type'] = tp

        # # Plot land residual results
        # plot_multiple(
        #     gdf=parcels_gdf.loc[:, [
        #         'residual_sqm_Townhouse',
        #         'residual_sqm_Low-Mid-Rise',
        #         'residual_sqm_High-Rise',
        #         'land_value_sqm',
        #         'geometry'
        #     ]],
        #     filepath=f'figures/{self.prefix}residual_land.png'
        # )
        #
        # # Plot height results
        # plot_multiple(
        #     gdf=parcels_gdf.loc[:, ['height_Townhouse', 'height_Low-Mid-Rise', 'height_High-Rise', 'geometry']],
        #     filepath=f'figures/{self.prefix}max_height.png'
        # )

        # Filter feasible parcels

        # parcels_gdf = parcels_gdf[parcels_gdf['feasible']]
        # assert len(parcels_gdf) > 0, AssertionError("No parcels feasible for development")

        # Plot feasible parcels
        # fig, ax = plt.subplots()
        # colors = {'Townhouse': 'lightgrey', 'Low-Mid-Rise': 'steelblue', 'High-Rise': 'midnightblue'}
        # for tp in parcels_gdf['type'].unique():
        #     parcels_gdf[parcels_gdf['type'] == tp].plot(ax=ax, legend=True, color=colors[tp]).set_axis_off()
        # parcels_gdf.plot(column='type', legend=True, figsize=(16, 16)).set_axis_off()
        # plt.savefig(f'figures/{self.prefix}feasible_parcels.png', transparent=True, dpi=100)

        neigh = self.neigh
        neigh.parcels.gdf = parcels_gdf.loc[:, out_cols]
        print(f"Feasible parcels filtered ({int(time.time() - start_time)}s)")
        return neigh

    def assemble_and_subdivide(self, street_width=10):
        start_time = time.time()
        gc.collect()
        neigh = self.neigh
        gdf = neigh.parcels.gdf.copy()

        # Assemble small parcels with large fsr
        cols = ['fsr_dist_power_rev', 'residual_land_Townhouse', 'residual_land_Low-Mid-Rise', 'residual_land_High-Rise',
                'feasible_Townhouse', 'feasible_Low-Mid-Rise', 'feasible_High-Rise', 'fsr','geometry']
        as_gdf = Shape(gdf.loc[:, cols]).dissolve(join_operations=['mean', 'sum'])

        # Get type information from unassembled parcels
        for i in as_gdf['parent_id'].unique():
            as_gdf.loc[as_gdf['parent_id'] == i, 'type'] = gdf.loc[i, 'type']
        as_gdf = as_gdf.drop('parent_id', axis=1)

        # Subdivide large parcels and create streets
        cols = ['fsr_dist_power_rev_mean', 'feasible_Townhouse_sum', 'feasible_Low-Mid-Rise_sum', 'feasible_High-Rise_sum',
                'residual_land_Townhouse_sum', 'residual_land_Low-Mid-Rise_sum', 'residual_land_High-Rise_sum', 'type', 'fsr_mean']
        shp = Shape(as_gdf[as_gdf.area > MAX_BLOCK], reset_index=False)
        sub_gdf = shp.subdivide_obb(max_area=MAX_BLOCK * (street_width/4))
        if len(sub_gdf) > 0:
            sub_gdf['geometry'] = sub_gdf.buffer(-street_width/2)
        else:
            sub_gdf['parent_id'] = []

        for i in sub_gdf['parent_id'].unique():
            for col in cols:
                sub_gdf.loc[sub_gdf['parent_id'] == i, col] = as_gdf.loc[i, col]
        neigh.parcels.gdf = pd.concat([as_gdf[as_gdf.area <= MAX_BLOCK], sub_gdf]).reset_index(drop=True)
        neigh.parcels.gdf['build_type'] = neigh.parcels.gdf['type']

        # Generate potential laneways
        if len(sub_gdf) > 0:
            shp2 = Shape(sub_gdf)
            shp2.subdivide_spine()
            lanes = gpd.GeoDataFrame({'geometry': shp2.meridian[0]})
            lanes['laneway'] = 1
        else:
            lanes = gpd.GeoDataFrame()

        # Rebuild network parameter adding new streets and intersections
        streets = gpd.GeoDataFrame({'geometry': shp.splitters}, crs=gdf.crs)
        streets['laneway'] = 0
        neigh.streets.gdf = pd.concat([streets, lanes])

        fig, ax = plt.subplots(figsize=(12, 12))
        neigh.parcels.gdf.plot(column='build_type', legend=True, ax=ax).set_axis_off()
        neigh.boundary.boundary.plot(edgecolor='black', ax=ax)
        plt.savefig(f'figures/{self.prefix}subdivisions.png', transparent=True, dpi=100)
        print(f"Parcels assembled and subdivided ({int(time.time() - start_time)}s)")
        return neigh

    def randomize_urban_form(self, types, seed=0):
        """

        :param types:
        :param constraints: List of constraints ranges
        :return:
        """

        urban_form = []  # Randomize urban form

        random.seed(seed)
        np.random.seed(seed)
        for tp in types:
            i = self.type_info['Type'].index(BLD_TYPES[tp])
            p_width = random.choice(RANGES['parcel_width'])
            b_depth = random.choice(RANGES['building_depth'])
            b_heights = (self.type_info['Height'])[i] / 3
            urban_form.append({'PrclW': p_width, 'BldgD': b_depth, 'Storeys': b_heights})

        parcels_gdf = self.neigh.parcels.gdf.copy()
        for i in parcels_gdf.index:
            random.seed(i)
            bld_type = random.choice(DEV_TYPES[parcels_gdf.loc[i, 'build_type']])
            parcels_gdf.loc[i, 'bld_type'] = bld_type

        return urban_form, parcels_gdf

    def generate_new_urban_forms(self):
        """
        Densify feasible 'zones'

        :param zone: Zone object (based on zoning bylaws)
        :param types: One or more of
        :param unit_mix:
        :param unit_count:
        :param site_id:
        :param b_size:
        :param bldg_types:
        :return:
        """

        parcels_gdf = self.neigh.parcels.gdf.copy()
        parcels_gdf['id'] = parcels_gdf.index
        parcels_gdf['area'] = parcels_gdf.area
        parcels_gdf['fsr'] = parcels_gdf['fsr_mean']
        parcels_gdf['max_fsr'] = parcels_gdf['fsr_mean']
        assert 'type' in parcels_gdf.columns, AssertionError("'type' column not found, filter_feasible_parcels first")
        assert 'build_type' in parcels_gdf.columns, AssertionError("'build_type' column not found, filter_feasible_parcels first")
        types = [i for sl in list(DEV_TYPES.values()) for i in sl]

        # Randomize urban form by type
        densified = gpd.GeoDataFrame()

        # Assign maximum heights and site coverage
        for tp in self.type_info['Type']:
            parcels_gdf['max_height_from_type'] = self.type_info['Height'][self.type_info['Type'].index(tp)]
            parcels_gdf['max_coverage'] = self.type_info['Occupancy'][self.type_info['Type'].index(tp)]
        parcels_gdf['max_height_from_fsr'] = height_from_fsr(parcels_gdf)['height']
        parcels_gdf['max_height'] = parcels_gdf.loc[:, ['max_height_from_type', 'max_height_from_fsr']].min(axis=1)
        self.neigh.parcels.gdf = parcels_gdf.copy()

        # Create development object
        dev = Development(parcel=parcels_gdf, fsr=parcels_gdf['max_fsr'],
                          units=pd.DataFrame(UNIT_MIX), site_coverage=parcels_gdf['max_coverage'],
                          max_height=parcels_gdf['max_height'])
                          # max_height=min(
                          #     self.type_info['Height'][self.type_info['Type'].index(parcels_gdf.loc[i, 'build_type'])],
                          #     height_from_fsr(parcels_gdf)['height']))

        # For each combination of maximum fsr and site coverage create development zone object and densify it
        parcels_gdf['dev_zone_params'] = 'fsr' + parcels_gdf['max_fsr'].astype(str) + 'cover' + parcels_gdf['max_coverage'].astype(str)
        for i, params in enumerate(parcels_gdf['dev_zone_params'].unique()):
            dev_parcels = parcels_gdf[(parcels_gdf['dev_zone_params'] == params)].copy()
            dev_parcels['court_depth'] = depth_from_coverage(dev_parcels)['court_depth']
            bldg_form, randomized_pcl = self.randomize_urban_form(types=types, seed=random.seed(i + 1))
            dev_parcels['bld_type'] = randomized_pcl['bld_type']
            # dev_parcels['Type'] = list(self.neigh.parcels.gdf.loc[dev_parcels.index, 'bld_type'])
            print(dev_parcels['bld_type'].unique())
            dev_zone = DevelopmentZone(
                development=dev,
                zone=Zone(
                    envelopes={'standard': Envelope([Box(10.7, 1.5, 1.5, 1.5), Box(60, 2, 1.5, 1.5)])},
                    fsr=dev_parcels['max_fsr'].unique()[0],
                    max_coverage=dev_parcels['max_coverage'].unique()[0],
                    neighborhood=Neighbourhood(
                        parcels=Parcels(dev_parcels, reset_index=False))),
                types=types,
                bldg_form=bldg_form,
                unit_mix=self.unit_mix,  # unit_count=unit_count,
                unit_count=int(sum(dev.unit_count())),
                whole_block=True,
                r_seed=i)
            dev_zone.neigh = Neighbourhood(parcels=Parcels(dev_parcels, reset_index=False))
            dev_zone.lanes = self.neigh.streets.gdf[self.neigh.streets.gdf['laneway'] == 1],
            buildings = dev_zone.densify(bldg_types=dev_parcels['bld_type'], site_id=dev_parcels['id'],
                                         subdivide=False, design=True, fixed_height=False)
            densified = pd.concat([densified, buildings])

        #
        # for i in tqdm(parcels_gdf.index): # Iterate over assembled parcels
        #     bldg_form = self.randomize_urban_form(types=types, seed=random.seed(i + 1))
        #     parcels_gdf.loc[i, 'type'] = self.neigh.parcels.gdf.loc[i, 'bld_type']
        #     site_coverage = self.type_info['Occupancy'][self.type_info['Type'].index(parcels_gdf.loc[i, 'build_type'])]
        #
        #     # Get building depth that maximizes allowed site coverage
        #     parcels_gdf.loc[i, 'coverage'] = site_coverage
        #     parcels_gdf.loc[[i], 'depth'] = depth_from_coverage(parcels_gdf.loc[[i], :])['depth']
        #
        #     # # Get maximum height based on fsr
        #     # parcels_gdf.loc[[i], 'height'] = height_from_fsr(parcels_gdf.loc[[i], :])['height']
        #
        #     # Modify building form to comply with regulations
        #     for d in bldg_form:
        #         d['BldgD'] = round(max(d['BldgD']*-1, parcels_gdf.loc[i, 'depth']) * -1, 2)
        #         # d['Storeys'] = min(d['Storeys'], parcels_gdf.loc[i, 'height']/3)
        #
        #     # Create Development Zone and densify it
        #     if sum(parcels_gdf.loc[[i], :].area) > 0:
        #         dev = Development(parcel=parcels_gdf.loc[[i], :], fsr=parcels_gdf.loc[i, 'fsr'],
        #                           units=pd.DataFrame(UNIT_MIX), site_coverage=site_coverage,
        #                           max_height=min(self.type_info['Height'][self.type_info['Type'].index(parcels_gdf.loc[i, 'build_type'])], height_from_fsr(parcels_gdf.loc[[i], :]).loc[i, 'height']))
        #         dev_zone = DevelopmentZone(
        #             development=dev,
        #             zone=Zone(
        #                 envelopes={'standard': Envelope([Box(10.7, 3.7, 1.5, 2)])},
        #                 max_coverage=site_coverage,
        #                 neighborhood=Neighbourhood(
        #                     parcels=Parcels(parcels_gdf, reset_index=False))),
        #             types=types,
        #             bldg_form=bldg_form,
        #             unit_mix=self.unit_mix, # unit_count=unit_count,
        #             unit_count=int(sum(dev.unit_count())),
        #             whole_block=True,
        #             r_seed=i)
        #         dev_zone.neigh = Neighbourhood(parcels=Parcels(parcels_gdf.loc[[i], :], reset_index=False))
        #         dev_zone.lanes = self.neigh.streets.gdf[self.neigh.streets.gdf['laneway'] == 1],
        #         buildings = dev_zone.densify(bldg_types=[parcels_gdf.loc[i, 'type']], site_id=parcels_gdf.loc[i, 'id'],
        #                                      subdivide=False, design=True, fixed_height=False)
        #         densified = pd.concat([densified, buildings])
        #     else:
        #         print("Generator error: No parcels found to densify")

        densified = self.neigh.join_parcel_id(densified)
        self.neigh.buildings = Buildings(densified)
        self.neigh.parcels.gdf = self.neigh.get_current_fsr()
        return self.neigh

    def predict_all_indicators(self):
        aff = AffordabilityAnalyzer(self.neigh.parcels.gdf, new_network)
        aff.gdf = aff.aggregate_spatial_indicators(f'{DIRECTORY}/{CITY}', AMENITY_LAYERS, RADII)

        # Classify cafe parcels based on spatial indicators
        aff.gdf = aff.predict_amenity_count()

        # Predict new rent price based on urban form
        aff.gdf = aff.predict_indicator()
   