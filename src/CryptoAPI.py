from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
import ENV
import SupportFunctions
	

def test_coinmarketcap_api():
	url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
	parameters = {
		'start':'1',
		'limit':'10'
	}
	headers = {
		'Accepts': 'application/json',
		'X-CMC_PRO_API_KEY': SupportFunctions.get_env_var(ENV.COINMARKETCAP_API_KEY_STRING, require_input=True, input_str="Please enter your CoinMarketCap API key: "),
	}

	session = Session()
	session.headers.update(headers)

	try:
		response = session.get(url, params=parameters)
		data = json.loads(response.text)
		print(data)
	except (ConnectionError, Timeout, TooManyRedirects) as e:
		print(e)

if __name__ == "__main__":
	test_coinmarketcap_api()
	print("ok")