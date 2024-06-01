import geopandas as gpd
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib import rc

crs = 26910

# Change default font
fm.fontManager.ttflist += fm.createFontList(['/Volumes/Samsung_T5/Fonts/sfrm1000.pfb.ttf'])
rc('font', family='Computer Modern', weight='medium')

# Load neighborhood boundaries
neigh = gpd.read_file('https://opendata.vancouver.ca/explore/dataset/local-area-boundary/download/?format=geojson&timezone=America/Los_Angeles&lang=en&epsg=26910')
neigh['id'] = neigh.index
neigh.crs = crs

# Load Craigslist and Census data
gpk = '/Volumes/Samsung_T5/Databases/Metro Metro Vancouver Regional District, British Columbia.gpkg'
access = gpd.read_file(gpk, layer='land_dissemination_area')
craig = gpd.read_file(gpk, layer='craigslist_rent')
craig = craig.to_crs(crs)

# Join data to neighborhoods
neigh['med_price_sqft'] = gpd.sjoin(neigh, craig.loc[:, ['price_sqft', 'geometry']], how='left').groupby('id').median()['price_sqft']
neigh['ave_active_mob'] = gpd.sjoin(neigh, access.loc[:, ['walk', 'bike', 'bus', 'geometry']]).groupby('id').mean().loc[:, ['walk', 'bike', 'bus']].sum(axis=1)

# Plot maps
plt.xticks(fontsize=9)
fig, ax = plt.subplots(ncols=2, figsize=(6, 3))
neigh.plot('med_price_sqft', ax=ax[0], cmap='Blues', legend=True, legend_kwds={
    'label': "Median Rent Price ($/Sq.Ft.)",
    'orientation': "horizontal"
})
neigh.plot('ave_active_mob', ax=ax[1], cmap='Blues', legend=True, legend_kwds={
    'label': "Walk, Cycle or Ride Transit (0-1)",
    'orientation': "horizontal"
})
ax[1].set_axis_off()
ax[1].set_title('Accessibility')
ax[0].set_axis_off()
ax[0].set_title('Affordability')
plt.tight_layout()
fig.savefig('../../PhD/Figures/neighborhoods_maps.png', dpi=300)

# Plot scatter plot
fig, ax = plt.subplots(figsize=(4, 3))
ax.scatter(x=neigh['ave_active_mob'], y=neigh['med_price_sqft'])
ax.set_xlabel('% Commuters that Walk, Cycle or Ride Transit to Work')
ax.set_ylabel('Median Rent Price ($/Sq.Ft.)')
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
plt.tight_layout()
fig.savefig('../../PhD/Figures/neighborhoods_scatter.png', dpi=300)
