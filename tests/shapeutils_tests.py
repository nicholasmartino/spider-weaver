import unittest
from shapeutils.GeoDataFrameUtils import *
from shapely.geometry import Polygon


class TestGDFContainsFunction(unittest.TestCase):

	def test_different_crs(self):
		# Create two GeoDataFrames with different CRS
		gdf1 = gpd.GeoDataFrame({
			'geometry': [Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])]
		}, crs="EPSG:4326")

		gdf2 = gpd.GeoDataFrame({
			'geometry': [Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])]
		}, crs="EPSG:3857")

		with self.assertRaises(ValueError):
			gdf_box_contains(gdf1, gdf2)

	def test_not_contained(self):
		# Create two GeoDataFrames where the second one is not completely within the first one
		gdf1 = gpd.GeoDataFrame({
			'geometry': [Polygon([(0, 0), (0, 5), (5, 5), (5, 0)])]
		}, crs="EPSG:4326")

		gdf2 = gpd.GeoDataFrame({
			'geometry': [Polygon([(4, 4), (4, 6), (6, 6), (6, 4)])]
		}, crs="EPSG:4326")

		self.assertFalse(gdf_box_contains(gdf1, gdf2))


if __name__ == "__main__":
	unittest.main()
