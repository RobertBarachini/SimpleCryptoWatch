import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import os
import config
import SupportFunctions as sf
import DataGrabber as dg

log = sf.set_logging("ServiceHandler")
machine = os.environ['COMPUTERNAME']

def is_installed(name):
	return service_status(name) != None
		
def is_running(name):
	rez = service_status(name)
	if rez and rez[1] == 4:
		return True
	else:
		return False
	# return rez and rez[1] == 4 # Returns None if rez is None

def service_status(name):
	try:
		log.info(f"Checking status for service '{name}'")
		rez = win32serviceutil.QueryServiceStatus(name, machine)
		log.info(f"Service '{name}' status: '{rez}'")
		return rez
	except Exception as e:
		log.error(e)
		return None
		# if "The specified service does not exist as an installed service" in str(e):
		# 	None

def start_service(name):
	 win32serviceutil.StartService(name, machine)

if __name__ == "__main__":
	name = "Windows Search"
	# name = "hmmmmmmmmmmmmmm"
	running = is_running(name)
	installed = is_installed(name)
	print(machine)
	print(f"Service {name} is running: {running} ; is installed: {installed}")