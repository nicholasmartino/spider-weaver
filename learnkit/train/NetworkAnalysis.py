import gc
import pickle
from shapely.ops import nearest_points
from tqdm import tqdm
import pandas as pd
from shapeutils.ShapeTools import SpatialAnalyst
from shapely.geometry import LineString, Point


class SpatialNetworkAnalyst:
	def __init__(self, analyst, network):
		self.left_gdf = analyst.left_gdf
		self.right_gdf = analyst.right_gdf
		self.network = network
		return

	def buffer_join_network(self, radius, decay='flat', operation='ave', columns=None):
		"""
		Aggregates data from the right_gdf located on the surroundings of the gdf elements according to a street network
		:return:
		"""
		self.right_gdf = self.__get_closest_node_id(left=False)
		right_gdf = self.__convert_categorical_to_numerical(left=False)
		left_gdf = self.__get_closest_node_id()

		columns_to_analyze = columns
		if columns is None:
			columns_to_analyze = [col for col in right_gdf.columns if col not in ['geometry', 'node']]

		self.__build_network()
		net = self.network.pdn_net
		net.precompute(radius)

		new_columns = []
		for col in columns_to_analyze:
			net.set(node_ids=right_gdf["node"], variable=right_gdf[col])
			agg = net.aggregate(distance=radius, type=operation, decay=decay)
			column_name = f"{col}_r{radius}_{operation}_{decay}"
			left_gdf[column_name] = list(agg.loc[left_gdf["node"]])
			new_columns.append(column_name)
			gc.collect()

		"""
		# Calculate diversity index for categorical variables
		if diversity:
			for k, v in uniques.items():
				simpson = True
				shannon = True
				print(f"> Calculating diversity index for {k}")
				for decay in decays:
					categories = [f"{category}_r{radius}_sum_{decay[0]}" for category in v if
								  category != "other"]
					for category in categories:
						try:
							del sample_gdf[f"{category}_r{radius}_ave_{decay[0]}"]
						except:
							pass
						try:
							del sample_gdf[f"{category}_r{radius}_rng_{decay[0]}"]
						except:
							pass
					gc.collect()
					cat_gdf = sample_gdf.loc[:, categories]
					if simpson: sample_gdf[
						f"{k}_r{radius}_si_div_{decay[0]}"] = div.alpha_diversity('simpson',
																							   cat_gdf)
					if shannon: sample_gdf[
						f"{k}_r{radius}_sh_div_{decay[0]}"] = div.alpha_diversity('shannon',
																							   cat_gdf)
				gc.collect()
		gc.collect()

		# Clean count columns
		for col in sample_gdf.columns:
			if ('_ct_' in col) & ('_cnt' in col): sample_gdf = sample_gdf.drop([col], axis=1)
			if ('_ct_' in col) & ('_ave' in col): sample_gdf = sample_gdf.drop([col], axis=1)
			gc.collect()
		"""

		return left_gdf.loc[:, new_columns]

	def get_distance_to_nearest(self, max_dist=1600, suffix='nearest'):
		"""
		Gets the distance from every element in the left gdf to closest element on right gdf
		:return:
		"""

		network = self.__build_network()
		network.precompute(max_dist)
		network.set_pois(
			category=suffix,
			maxdist=max_dist,
			maxitems=2,
			x_col=self.right_gdf.centroid.x,
			y_col=self.right_gdf.centroid.y)
		dist = network.nearest_pois(distance=max_dist, category=suffix, num_pois=2).drop([1], axis=1)
		distance_columns = [f'd2_{suffix}']
		dist.columns = distance_columns

		gdf = self.__get_closest_node_id()
		dist['node'] = dist.index
		gc.collect()
		return pd.merge(left=gdf, right=dist, how="left", on="node", copy=True).loc[:, distance_columns]

	def __build_network(self, rebuild=False):
		assert self.network is not None, AttributeError("Analyst object has no attribute 'network'")
		if (self.network.pdn_net is None) or rebuild:
			self.network.pdn_net = self.network.build()
		return self.network.pdn_net

	def __get_closest_node_id(self, left=True):
		"""
		Gets the closest node of left or right GeoDataFrame to network
		:param left:
		:return:
		"""

		net = self.__build_network()

		if left:
			gdf = self.left_gdf
		else:
			gdf = self.right_gdf

		gdf['node'] = net.get_node_ids(gdf.geometry.centroid.x, gdf.geometry.centroid.y)
		return gdf

	def __convert_categorical_to_numerical(self, left=True):

		if left:
			gdf = self.left_gdf
		else:
			gdf = self.right_gdf

		for col in [col for col in gdf.columns if col != 'geometry']:
			try:
				gdf[col] = pd.to_numeric(gdf[col])
			except:
				for item in gdf[col].unique():
					gdf.loc[gdf[col] == item, item] = 1
				gdf = gdf.drop(col, axis=1)
				gdf = gdf.fillna(0)
		return gdf

	@staticmethod
	def aggregate_spatial_indicators(target_gdf, network_gdf, radius):
		target_gdf = target_gdf.copy()

		analysts = {}
		for key, values in tqdm(layers.items()):
			analysts[key] = SpatialAnalyst(
				target_gdf,
				gpd.layer_exists(f'{directory}/{key}.feather').loc[:, values + ['geometry']].to_crs(gdf.crs),
				network=network_gdf)

		for key, values in tqdm(layers.items()):
			target_gdf = analysts[key].buffer_join_network(radius=radius, operations=['ave', 'sum'])

		return target_gdf

	@staticmethod
	def get_distance_to_amenities(target_gdf, network_gdf, amenities_gdf, max_dist=1000):
		gdf = target_gdf.copy()

		assert 'amenity' in amenities_gdf.columns
		for amenity in tqdm(list(amenities_gdf['amenity'].unique())[:50]):
			analyst = SpatialAnalyst(gdf, amenities_gdf[amenities_gdf['amenity'] == amenity].copy(), network=network_gdf)
			# - Get distance indicators (d2amenities and d2cbd)
			gdf = analyst.get_distance_to_nearest(max_dist=max_dist, max_items=2, suffix=amenity)
			gc.collect()
		return gdf

	@staticmethod
	def get_distance_to_cbd(target_gdf, cbd_gdf):
		gdf = target_gdf.copy()
		cbd = list(cbd_gdf['geometry'])[0].centroid
		gdf['d2cbd'] = [
			(ctr.x - cbd.x) * (ctr.x - cbd.x) + (ctr.y - cbd.y) * (ctr.y - cbd.y)
			for ctr in tqdm(gdf.centroid)
		]
		return gdf

	def join_bc_assessment_data(self, bca_gdf):
		gdf = self.gdf.copy()
		analyst = SpatialAnalyst(gdf, bca_gdf)
		gdf = analyst.spatial_join(operations=['mean', 'sum'])  # - Get structural indicators (spatial join from BCA)
		return gdf

	def predict_indicator(self, indicators, model_dir=''):
		gdf = self.gdf.copy()
		for dependent in indicators:
			pre = pickle.load(open(f'{model_dir}/predictor-{dependent}.pkl', 'rb'))

			# Predict residential rent prices
			columns = [col for col in pre.data.columns if col not in indicators]

			diff = set(columns).difference(set(self.gdf.columns))
			assert len(diff) == 0, AssertionError(f"{diff} not found in analyzer's GeoDataFrame")

			gdf = gdf.loc[:, columns].dropna()
			assert len(gdf) > 0, AssertionError(f"Analyzer GeoDataFrame is empty after removing null items")

			self.gdf.loc[gdf.index, dependent] = pre.predict(gdf)

			print(f"Average {dependent}: {self.gdf[dependent].mean()}")

		# reg.train_data = {dependent: self.gdf.loc[:, orig_train_data.columns]}
		# reg.cur_method = pickle.load(open(f'{model_dir}/{dependent}_Method.sav', 'rb'))
		# reg.fitted = pickle.load(open(f'{model_dir}/{dependent}_FittedModel.sav', 'rb'))

		# self.gdf[dependent] = reg.pre_norm_exp(gdf)[f'{dependent}_rf']
		return self.gdf

	def update_rent_price(self, cl_gdf):
		pcl = self.gdf.copy()
		craig = cl_gdf.to_crs(26910)

		# Snap Craigslist data to closest pcl
		all_parcels = pcl.unary_union
		print("> Snapping Craigslist data to parcels layer")
		craig['geometry'] = [nearest_points(geom, all_parcels)[1].buffer(10) for geom in tqdm(craig['geometry'])]
		pcl['id'] = pcl.index

		# Join data from craigslist to parcels layer
		print("> Joining Craigslist data to parcels layer")
		gdf = SpatialAnalyst(pcl, craig.loc[:, ['price_bed', 'geometry']]).spatial_join()
		return gdf


class NetworkMetricsCalculator:

	def __init__(self, gdf):
		self.gdf = gdf

	def calculate_metrics(self):
		self.__calculate_length()
		self.__calculate_straightness()
		return self

	def __calculate_length(self):
		gdf = self.gdf.copy()
		gdf['length'] = gdf.length
		self.gdf = gdf
		return self

	def __calculate_straightness(self):
		gdf = self.gdf.copy()
		# Calculate street segment in relation to the shortest line from start to end of segment
		print("> Calculating shortest path")
		shortest = []
		for i, segment in zip(gdf.index, gdf['geometry']):
			if segment.__class__.__name__ == 'LineString':
				shortest.append(LineString([Point(segment.coords[0]), Point(segment.coords[1])]).length)
			elif segment.__class__.__name__ == 'MultiLineString':
				shortest.append(LineString([Point(segment[0].coords[0]), Point(segment[0].coords[1])]).length)
				gdf.at[i, 'geometry'] = segment[0]

		gdf['shortest'] = shortest

		# Calculate straightness
		print("> Calculating straightness")
		gdf['straightness'] = gdf['shortest'] / gdf['length']

		self.gdf = gdf
		return self
