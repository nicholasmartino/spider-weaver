import gc

import matplotlib.pyplot as plt


def plot_choropleth_map(gdf, column, directory, gray_gdf=None):
    if column not in gdf.columns:
        raise ValueError(f"Column '{column}' not found in GeoDataFrame")

    _, ax = plt.subplots(1, 1, figsize=(10, 8))

    if gray_gdf is not None:
        gray_gdf.plot(
            ax=ax, 
            color='lightgray', 
            linewidth=0.2, 
            zorder=0)

    plot_gdf = gdf[gdf[column] != 0]
    plot_gdf.plot(
        column=column, 
        ax=ax, 
        cmap='magma_r', 
        legend=True, 
        scheme="NaturalBreaks", 
        zorder=1)

    # Set the axis limits to the bounding box of gdf
    ax.set_xlim(gdf.total_bounds[0], gdf.total_bounds[2])
    ax.set_ylim(gdf.total_bounds[1], gdf.total_bounds[3])
    ax.set_axis_off()

    plt.tight_layout()
    plt.savefig(f"{directory}/{column.replace('/', '_')}_map.png", dpi=150)
    plt.close()
    gc.collect()
