import matplotlib.pyplot as plt


def plot_choropleth_map(gdf, column, directory):
    if column not in gdf.columns:
        raise ValueError(f"Column '{column}' not found in GeoDataFrame")
    fig, ax = plt.subplots(1, 1)
    gdf.plot(column=column, ax=ax, legend=True)
    plt.savefig(f"{directory}/{column}_map.jpg")
