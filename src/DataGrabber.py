# Used for getting data from different API endpoints and writing it to the DB
# Runs as a service

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

# Gets called by the SimpleCryptoService periodically
def update_coinmarketcap_listings():
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

if __name__ == "__main__":
	update_coinmarketcap_listings()
	print("All finished in DataGrabber.")
