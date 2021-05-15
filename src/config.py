# Stores 'global' config variables

environment = "debug" # debug / production
interval_coinmarketcap = 5 * 60 # Refresh interval for coinmarketcap in seconds
tablename_livelistings = "live_listings"
coinmarketcap_limit = 100
# Service version should be incremented by 1 each time the service is updated to
# ensure automatic reinstallation of the client
service_crypto = {"version": 1, "name": "SimpleCryptoWatch", "display_name": "SimpleCryptoWatch", "description": "This service is used for the SimpleCryptoWatch program. It enables continuous data fetching from various crypto APIs."}
 