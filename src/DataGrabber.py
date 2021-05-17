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
import config

log = sf.set_logging("DataGrabber")

# def get_crypto_list():

def save_crypto_mapping(data):
	log.info(f"Saving '{len(data)}' crypto mappings into '{config.tablename_cryptomap}'")
	for cmap in data:
		db.insert_into(config.tablename_cryptomap, '(id, name, symbol, slug, data) values (%s, %s, %s, %s, %s)', [cmap["id"], cmap["name"], cmap["symbol"], cmap["slug"], db.Json(cmap)], auto_commit=True)
	# TODO disable autocommit parameter and commit 'by hand' or change to insert many at the same time
	log.info("Saved crypto mappings")

# Used to get and update coinmarketcap crypto id mapping
# If ids are provided it filters by ids TODO
# If names are proveded it filters by names TODO
def get_cryptomap(ids=None, names=None):
	log.info(f"Creating table '{config.tablename_cryptomap}' if it doesn't exist.")
	db.create_table(config.tablename_cryptomap, "id integer PRIMARY KEY, name text, symbol text, slug text, data json")
	log.info("Getting Coinmarketcap crypto mapping")
	data = None
	data = db.select_from(config.tablename_cryptomap)
	if not data:
		data = ca.get_cryptomapping()
		if data and data["status"]["error_code"] == 0:
			save_crypto_mapping(data["data"])
		else:
			log.info(f"Trouble fetching crypto mapping. Data: {data}")
	log.info("Updated Coinmarketcap crypto mapping.")
	return data
	# TODO return suggested time to wait before next repeated call 

def save_crypto_listing(data):
	db.insert_into(config.tablename_livelistings, '(datetime_added, data) values (%s, %s)', [dt.datetime.now(), db.Json(data)])

# Used to get and update live listings data
# Gets called by the SimpleCryptoService periodically
def get_coinmarketcap_listings():
	log.info(f"Creating table '{config.tablename_livelistings}' if it doesn't exist.")
	db.create_table(config.tablename_livelistings, "id serial PRIMARY KEY, datetime_added timestamptz, data json")
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
	return data
	# TODO return suggested time to wait before next repeated call 

if __name__ == "__main__":
	# data = get_coinmarketcap_listings()
	data = get_cryptomap()
	print("All finished in DataGrabber.")
