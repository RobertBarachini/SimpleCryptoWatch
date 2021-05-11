import os
import config
# from dotenv import load_dotenv

# TODO fix logging in separate files as done in https://stackoverflow.com/questions/11232230/logging-to-two-files-with-different-settings
def set_logging(logging, filename):
	if not os.path.isdir("logs"):
		os.makedirs("logs")
	level = None
	if config.environment == "debug":
		level = logging.INFO
	else: 
		level = logging.DEBUG
	# encoding can be used with Python 3.9, not 3.7 ; encoding='utf-8'
	logging.basicConfig(filename=f'logs/{filename}.log', level=level, filemode="a+", format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
	logging.info(f"Set up logging for '{filename}' with level '{level}'")

def get_env_var(varname, require_input=False, input_str=None):
	try:
		val = os.environ.get(varname)#ENV.API_KEY_STRING)
		if require_input and (val == None or len(val) == 0):
			val = input_env_var(varname, input_str=input_str)
		return val
	except:
		print("Error getting '{varname}' environmental variable.")

def set_env_var(varname, varval):
	os.environ[varname] = str(varname)
	# Add the variable name and key to the .env file
	try:
		with open(".env", "a+") as f:
			f.write("%s=\"%s\"%s" % (varname, varval, os.linesep))
	except Exception:
		print("Error writing to .env file...")
	
def input_env_var(varname, input_str=None):
	input_str = "Please enter the value for the '{varname}' environmental variable." if input_str == None else input_str
	val = input(input_str)
	set_env_var(varname, val)
	return val

# Inits the .env file with all variable keys with empty values - user should add API keys and such after
def private_env_setup():
	if not os.path.exists(".env"):
		import ENV
		for var in ENV.__dict__:
			if "__" not in var:
				neki = ENV.__dict__[var]
				set_env_var(neki, "")

if __name__ == "__main__":
	# private_env_setup()
	None