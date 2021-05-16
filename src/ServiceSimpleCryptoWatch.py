# TODO supply a root directory when installing a service
# to avoid CWD issues

import os
script_path = os.path.dirname(os.path.realpath(__file__))
print(f"CWD set to '{script_path}'")
os.chdir(script_path)
import time
from SMWinservice import SMWinservice
import config
import SupportFunctions as sf
import DataGrabber as dg
import DatabaseConnector as db
import sys

log = sf.set_logging("ServiceSimpleCryptoWatch")
log.info("Initiating service file.")

class SimpleCryptoWatchService(SMWinservice):
	log.info("Setting variables")
	# from threading import Event
	# exit_event = Event()

	_svc_name_ = config.service_crypto["name"]
	_svc_display_name_ = config.service_crypto["display_name"]
	_svc_description_ = f"{config.service_crypto['description']} ; Service version: {config.service_crypto['version']}"

	# import signal
	# signal.signal(getattr(signal, "SIGTERM"), quit_this)
	log.info("Done setting variables")

	def start(self):
		log.info("Starting service")

		# log.info("Setting signals")
		# import signal
		# signames = ['SIGTERM', 'SIGHUP', 'SIGINT']
		# for sig in signames:
		# 	try:
		# 		signal.signal(getattr(signal, sig), self.quit_this)
		# 	except Exception as e:
		# 		log.error(e)
		# log.info("Set signals")

		self.isrunning = True

	def stop(self):
		log.info("Stopping service")
		self.isrunning = False
		# log.info("Calling quit")
		# quit(0)
		# sys.exit(0)
		# raise SystemExit(0)

	def main(self):
		log.info("Started main")
		db.create_table(config.tablename_livelistings, "id serial PRIMARY KEY, datetime_added timestamptz, data json")
		while self.isrunning: #not exit_event.is_set() and self.isrunning:
			log.info("Updating Coinmarketcap live listings")
			dg.update_coinmarketcap_listings()
			# time.sleep(config.interval_coinmarketcap)
			# TODO add the time it takes to finish dg.update... into account when computing time to sleep
			# TODO use events/interrupts to quit
			# TODO get how long you should wait from update_coinmarketcap_listings
			log.info("Updated Coinmarketcap live listings")
			max_time_to_wait = round(config.interval_coinmarketcap)
			log.info(f"Max wait time set to '{max_time_to_wait}'")
			for i in range(0, max_time_to_wait):
				if not self.isrunning:
					break
				time.sleep(1)
			# exit_event.wait(config.interval_coinmarketcap)
		log.info("Finishing up...")

	# def quit_this(self, signo, _frame):
	# 	log.info(f"Interrupted by '{signo}'', shutting down ; _frame='{_frame}'")
	# 	exit_event.set()

if __name__ == "__main__":
	log.info("In '__main__'")
	SimpleCryptoWatchService.parse_command_line()
	print("All finished in service.")
