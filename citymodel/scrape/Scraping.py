# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 13:52:23 2019

@author: nicholas-martino
"""

import datetime
import time
from Local import BritishColumbia
from Scraper import GeoScraper, Vancouver, Canada
from _Settings import regions, sites


if __name__ == '__main__':
    print(f"Start @ {datetime.datetime.now()}")
    for i in range(100000):

        for key, value in regions.items():
            date_list = [str((datetime.datetime(2020, 1, 31) - datetime.timedelta(days=x)).date()) for x in range(30)]

            # Create class
            bc = BritishColumbia(cities=value['British Columbia'])

            # Get city-wide data
            for city, cs_site in zip(bc.cities, sites):
                scraper = GeoScraper(city=city)
                # scraper.plot_craigslist_data()
                mov = scraper.movement_osm_gps(run=False)  # OpenStreetMaps
                emp = scraper.employment_indeed(False)  # Indeed

                try:
                    clh = scraper.housing_craigslist(cs_site, 900, run=True)  # Craigslist
                except:
                    print("Craigslist data not downloaded")
                print('###')

            # Get country-wide data
            country = Canada(provinces=[bc])
            country.update_databases(census=False)  # StatsCan

        # Scrape development permits at the Metro Vancouver Regional District webpage
        van = Vancouver('/Volumes/Samsung_T5/Databases/Permits/')
        van.scrape_rezoning(run=False)
        van.get_url_pdfs(run=False, url='https://development.vancouver.ca/')
        van.close_session()

        print(f"Finished @ {datetime.datetime.now()}")
        time.sleep(7200)
