from Analyzer import *
from Variables import *
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from ...shapeutils.ShapeTools import SpatialAnalyst
from Predictor import Predictor


def train_random_forest_regression(gdf, dependents, explanatory, rename_mask=None, random_state=0):

    unused_cols = list(set.difference(set(gdf.columns), set(dependents+explanatory)))
    if len(unused_cols) > 0:
        backup = gdf.copy().loc[:, unused_cols]

    if rename_mask is None: rename_mask = {}

    rename_mask2 = {}
    for k, v in rename_mask.items():
        for r in RADII:
            for d in ['l', 'f']:
                for op in ['ave', 'sum', 'cnt', 'rng']:
                    if op == 'ave':
                        t = 'Average'
                    elif op == 'sum':
                        t = 'Total'
                    elif op == 'rng':
                        t = 'Range'
                    else:
                        t = ''
                    renamed = f'{t} '
                    item = f'{renamed}{v.lower()} within {r}m'
                    rename_mask2[f"{k}_r{r}_{op}_{d}"] = f'{item.strip()[0].upper()}{item.strip()[1:]}'
    rename_mask = {**rename_mask, **rename_mask2}

    # # Read dependent variables
    # print("> Reading dependent parameters maps")
    # dep_gdf_raw = gdf
    # dep_columns = [e[0] for sl in [e for sl in dependent.values() for e in sl] for e in sl]

    # # Extract dependent values rename dictionary
    # dep_rename = {e[0]:e[1] for sl in [e for sl in dependent.values() for e in sl] for e in sl}
    # not_found = [col for col in dep_columns if col not in dep_gdf_raw.columns]
    # print(f"{len(not_found)} feature(s) not found – {not_found}")
    # dep_gdf = dep_gdf_raw.loc[:, dep_columns]

    # Read independent variables - Network analysis
    gdf = gdf.loc[:, explanatory + dependents]
    # ind_cols = [k for k in gdf.columns if 'aff' in k] + morph_cols + [
    #     'year_built', 'number_of_bedrooms', 'number_of_storeys', 'area_sqkm', 'bldg_count', 'land_size',
    # ]

    gdf = gdf.fillna(0)

    for dependent in dependents:
        predictor = Predictor(data=gdf, predictors=explanatory, predicted=dependent, random_state=random_state, percentile=98)
        predictor.split()
        predictor.regressor = predictor.train()
        predictor.test(plot_dir=f'{OUT_DIR}/figures')
        predictor.save(f'{OUT_DIR}/models')

    # reg = Regression(
    #     test_split=0.2,
    #     n_indicators=5,
    #     round_f=4,
    #     norm_x=False,
    #     norm_y=False,
    #     data=[gdf],
    #     directory=OUT_DIR,
    #     predicted=dependent,
    #     rename=rename_mask,
    #     filter_pv=False,
    #     dpi=DPI
    # )

    # # Run random forest and partial dependence plots
    # reg.non_linear(method=RandomForestRegressor)
    # reg.test_non_linear(i_method='regular')
    # reg.partial_dependence(n_features=9)
    # reg.save_model()
    return

def train_random_forest_classifier(gdf, dependent, explanatory):

    return



"""
# Define data to be aggregated on Sankey
radii = list(RADII)
imp_dfs = pd.DataFrame()
for key, imp_df in reg.feat_imp.items():
    # Set index to be feature code
    imp_df.index = imp_df['feature'].values
    # Assign y-parameters
    imp_df['dependent'] = key
    # Extract morph indicator type
    imp_df['ind_type'] = [f[:3] for f in imp_df['feature']]
    for f in imp_df.feature:
        for r in radii:
            if f"_r{r}_" in f:
                imp_df.at[f, 'feat'] = f.split(f"_r{r}_")[0]
                imp_df.at[f, 'radius'] = r
                imp_df.at[f, 'decay'] = f[-1:]
    imp_dfs = pd.concat([imp_dfs, imp_df])

# Visualize dependencies separated by categories
sankey = go.Figure()
source = []
target = []
values = []
cols = ['dependent', 'ind_type', 'feat', 'radius', 'decay']
to_group = 'dependencies'

# Group dependencies by feature
imp_dfs_cl = imp_dfs.drop(['feature'], axis=1).groupby(cols, as_index=False).mean()
imp_dfs_cl = imp_dfs_cl[imp_dfs_cl[to_group] > imp_dfs_cl[to_group].quantile(0.9)].reset_index(drop=True)
imp_dfs_cl = imp_dfs_cl.sort_values(by=to_group)

print(f"> Iterating over {cols} to construct nodes")
nodes = []
imps = []
for col in cols:
    for un in imp_dfs_cl[col].unique():
        nodes.append(un)
        imps.append(imp_dfs_cl[imp_dfs_cl[col] == un][to_group].sum())
nodes = pd.DataFrame({'label': nodes, 'value': imps})

print(f"> Iterating over {cols} to construct links by sources, targets and values")
for i, col in enumerate(cols):
    if i != len(cols) - 1:
        n_col = cols[i + 1]
        for col_un in imp_dfs_cl[col].unique():
            for n_col_un in imp_dfs_cl[n_col].unique():
                if (col_un in list(nodes['label'])) and (n_col_un in list(nodes['label'])):
                    source.append(nodes[nodes['label'] == col_un].index[0])
                    target.append(nodes[nodes['label'] == n_col_un].index[0])
                    values.append(imp_dfs_cl.loc[(imp_dfs_cl[col] == col_un) & (imp_dfs_cl[n_col] == n_col_un)][to_group].sum())

print(f"> Renaming columns")
nodes = nodes.replace(rename_mask)

print(f"> Creating sankey diagram with {len(source)} sources, {len(target)} targets and {len(values)} values")
plot = False
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=nodes['label'],  # ["A1", "A2", "B1", "B2", "C1", "C2"],
        color='#245C7C'
    ),
    link=dict(
        source=source,
        target=target,
        value=values
    ))])
fig.update_layout(title_text=f"Summed {to_group.title()}", font_size=10)
if plot: offline.plot(fig, filename=f'{DIRECTORY}sankey.html')

# Predict missing data
print("> Predicting missing data")
missing = aff_gdf[aff_gdf['price_bed'].isna()].loc[:, ind_cols]
predicted = reg.predict(x_dict={label_col: aff_gdf.loc[aff_gdf['price_bed'].isna(), reg.train_data[label_col].columns]
                                for label_col in reg.label_cols})
predicted['price_bed'] = reg.y_scaler.inverse_transform(predicted['price_bed'].reshape(-1, 1))
aff_gdf['geometry'] = parcels_geom
aff_gdf.loc[aff_gdf['price_bed'].isna(), dep_cols] = predicted['price_bed']
aff_gdf.set_geometry('geometry').to_file(f'{DIRECTORY}{CITY}.gpkg', layer='land_parcels_price', driver='GPKG')
"""