# Used for getting data from different API endpoints and writing it to the DB

import CryptoAPI as ca
import config
import time
import ENV
import SupportFunctions as sf
# import logging as log
import DatabaseConnector as db
import json
import datetime as dt
import time

log = sf.set_logging("DataGrabber")

# def get_crypto_list():

def save_crypto_listing(data):
	db.insert_into(config.tablename_livelistings, '(datetime_added, data) values (%s, %s)', [dt.datetime.now(), db.Json(data)])

def main_loop():
	# TODO actually do this stuff with events not thread.sleep or something like that
	db.create_table(config.tablename_livelistings, "id serial PRIMARY KEY, datetime_added timestamptz, data json")
	while True:
		log.info("Updating Coinmarketcap live listings.")
		data = None
		data = db.select_last(config.tablename_livelistings)
		time_diff = (dt.datetime.now().astimezone() - data[1]).total_seconds()
		if not data or time_diff >= config.interval_coinmarketcap:
			data = ca.get_live_listings_coinmarketcap()
			if data and data["status"]["error_code"] == 0:
				save_crypto_listing(data)
			else:
				log.info(f"Trouble fetching live listings. Data: {data}")
		else:
			data = data[2]
		log.info("Updated Coinmarketcap live listings.")
		break
		time.sleep(config.interval_coinmarketcap)

if __name__ == "__main__":
	main_loop()
	print("All finished in DataGrabber.")