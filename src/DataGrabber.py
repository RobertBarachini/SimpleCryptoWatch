# Used for getting data from different API endpoints and writing it to th DB

import CryptoAPI as ca
import config
import time
import SupportFunctions as sf
import logging as log
import DatabaseConnector as db

sf.set_logging(log, "DataGrabber")

# def get_crypto_list():

def main_loop():
	# TODO actually do this stuff with events not thread.sleep or something like that
	# TODO add DB support
	while True:
		log.info("Updating Coinmarketcap live listings.")
		data = ca.get_live_listings_coinmarketcap()
		# TODO save this stuff to DB
		log.info("Updated Coinmarketcap live listings.")
		time.sleep(config.interval_coinmarketcap)


if __name__ == "__main__":
	print("lol")