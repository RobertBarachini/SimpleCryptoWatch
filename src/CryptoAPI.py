from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
import ENV
import SupportFunctions as sf
import logging as log
import config

sf.set_logging(log, "CryptoAPI")

def get_data_coinmarketcap(url, parameters=None):
	headers = {
		'Accepts': 'application/json',
		'X-CMC_PRO_API_KEY': sf.get_env_var(ENV.COINMARKETCAP_API_KEY, require_input=True, input_str="Please enter your CoinMarketCap API key: "),
	}
	session = Session()
	session.headers.update(headers)
	data = None
	try:
		log.info("Getting data from Coinmarketcap.")
		response = session.get(url, params=parameters)
		log.info("Got data from Coinmarketcap.")
		data = json.loads(response.text)
	except (ConnectionError, Timeout, TooManyRedirects) as e:
		log.error(e)
		log.error(f"url='{url}', parameters='{parameters}'")
	return data

def get_credit_info_coinmarketcap():
	log.info("Checking Coinmarketcap credits.")
	url = "https://pro-api.coinmarketcap.com/v1/key/info"
	data = get_data_coinmarketcap(url)
	return data

def get_live_listings_coinmarketcap(parameters={'limit':f'{config.coinmarketcap_limit}','convert':'EUR'}):
	log.info("Checking Coinmarketcap live listings.")
	url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
	data = get_data_coinmarketcap(url, parameters)
	return data
	
# TODO
# Create a folder named 'temp' and store all last request results there in json
if __name__ == "__main__":
	data = None
	# data = get_live_listings_coinmarketcap()
	data = get_credit_info_coinmarketcap()
	print("ok")