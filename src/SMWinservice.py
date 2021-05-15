'''
SMWinservice
by Davide Mastromatteo ; http://thepythoncorner.com/dev/how-to-create-a-windows-service-in-python/

Base class to create winservice in Python
-----------------------------------------

Instructions:

1. Just create a new class that inherits from this base class
2. Define into the new class the variables
   _svc_name_ = "nameOfWinservice"
   _svc_display_name_ = "name of the Winservice that will be displayed in scm"
   _svc_description_ = "description of the Winservice that will be displayed in scm"
3. Override the three main methods:
    def start(self) : if you need to do something at the service initialization.
                      A good idea is to put here the inizialization of the running condition
    def stop(self)  : if you need to do something just before the service is stopped.
                      A good idea is to put here the invalidation of the running condition
    def main(self)  : your actual run loop. Just create a loop based on your running condition
4. Define the entry point of your module calling the method "parse_command_line" of the new class
5. Enjoy
'''

import socket
import win32serviceutil
import servicemanager
import win32event
import win32service

import SupportFunctions as sf
log = sf.set_logging("SMWinservice")

class SMWinservice(win32serviceutil.ServiceFramework):
	'''Base class to create winservice in Python'''

	log.info("Setting up variables")
	_svc_name_ = 'pythonService'
	_svc_display_name_ = 'Python Service'
	_svc_description_ = 'Python Service Description'

	@classmethod
	def parse_command_line(cls):
		'''
		ClassMethod to parse the command line
		'''
		log.info(f"Handling parse command line '{cls}'")
		win32serviceutil.HandleCommandLine(cls)
		log.info("Handled command line")

	def __init__(self, args):
		'''
		Constructor of the winservice
		'''
		log.info(f"Args: '{args}'")
		win32serviceutil.ServiceFramework.__init__(self, args)
		self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
		socket.setdefaulttimeout(60)

	def SvcStop(self):
		'''
		Called when the service is asked to stop
		'''
		log.info("ScvStop")
		self.stop()
		log.info("Reporting service status")
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		log.info(f"Setting '{hWaitStop}' event")
		win32event.SetEvent(self.hWaitStop)
		log.info("Set stop event")
		log.info("Calling quit")
		quit(0)

	def SvcDoRun(self):
		'''
		Called when the service is asked to start
		'''

		self.start()
		servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
													servicemanager.PYS_SERVICE_STARTED,
													(self._svc_name_, ''))
		self.main()

	def start(self):
		'''
		Override to add logic before the start
		eg. running condition
		'''
		pass

	def stop(self):
		'''
		Override to add logic before the stop
		eg. invalidating running condition
		'''
		pass

	def main(self):
		'''
		Main class to be ovverridden to add logic
		'''
		pass

# entry point of the module: copy and paste into the new module
# ensuring you are calling the "parse_command_line" of the new created class
if __name__ == '__main__':
	SMWinservice.parse_command_line()