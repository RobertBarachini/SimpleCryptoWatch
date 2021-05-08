# Handles DB connections and CRUD operations

import ENV
import SupportFunctions as sf
import psycopg2
import json
import logging as log
import config

sf.set_logging(log, "DatabaseConnector")

conn = None
cur = None

def create_db(database, user, password, host, port):
	global conn
	global cur
	try:
		log.info("Creating DB " + database)
		conn = psycopg2.connect(user=user, password=password, host=host, port=port)
		cur = conn.cursor()
		# In order to create a db we need to set autocommit to True
		conn.autocommit = True
		db_string = "CREATE DATABASE " + database
		cur.execute(db_string)
		conn.autocommit = False
		log.info("Created DB " + database)
	except Exception as e:
		log.error(f"Unable to create the DB with arguments: database='{user:s}', password='XXX', host='{host:s}', port='{port:s}'")
		raise e

def init_conn(database, user, password, host, port, can_create=True):
	global conn
	global cur
	try:
		conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
		cur = conn.cursor()
	except Exception as e:
		log.error(e)
		# If connection was established but the database does not exist we can try to create it and retry
		# otherwise throw exception
		if can_create and "does not exist" in str(e):
			create_db(database, user, password, host, port)
			# Retry connection
			init_conn(database, user, password, host, port, can_create=False)
		else:
			log.error(e)
			raise e

log.info("Initiating DB connection.")
init_conn(database=sf.get_env_var(ENV.DB_NAME), 
					user=sf.get_env_var(ENV.DB_USER), 
					password=sf.get_env_var(ENV.DB_PASS), 
					host=sf.get_env_var(ENV.DB_HOST),
					port=sf.get_env_var(ENV.DB_PORT))
log.info("Initiated DB connection.")

# def read_json(table_name, query=None):
# 	if query == None:
# 		query = "SELECT * FROM

def create_table(name, data):
	tx = f"CREATE TABLE IF NOT EXISTS {name} ({data});"
	try:
		log.info(f"Creating TABLE '{name}' with data '{data}'")
		cur.execute(tx)
		conn.commit()
	except Exception as e:
		log.error(e)
		log.error(f"Tx: {tx}")
		rollback()

def drop_table(name):
	try:
		log.info(f"Dropping TABLE '{name}'")
		cur.execute(f"DROP TABLE IF EXISTS {name};")
		conn.commit()
	except Exception as e:
		log.error(e)

def rollback():
	try:
		log.info("Rollback started")
		conn.rollback()
		log.info("Rollback finished")
	except Exception as e:
		log.error(e)
		raise e

def insert_into(name, data, auto_commit=True):
	tx = f"INSERT INTO {name} {data};"
	try:
		log.info(f"Inserting into table '{name}' data={data}")
		cur.execute(tx)
		if auto_commit:
			conn.commit()
	except Exception as e:
		log.error(e)
		log.error(f"Tx: {tx}")
		# You did an oopsie - try to rollback
		# if "commands ignored until end of transaction block" in str(e):
		rollback()

def select_from(name, nrows=-1):
	tx = f"SELECT * FROM {name};"
	try:
		log.info(f"Selecting from table '{name}'")
		cur.execute(tx)
		rez = None
		if nrows == -1:
			rez = cur.fetchall()
		elif nrows == 1:
			# same as cur.fetchmany(size=cur.arraysize)
			rez = cur.fetchone() 
		else:
			rez = cur.fetchmany(size=nrows)
		return rez
	except Exception as e:
		log.error(e)
		log.error(f"Tx: {tx}")
		rollback()


def basic_db_test():
	conn = psycopg2.connect(database=sf.get_env_var(ENV.DB_NAME), 
													user=sf.get_env_var(ENV.DB_USER), 
													password=sf.get_env_var(ENV.DB_PASS), 
													host=sf.get_env_var(ENV.DB_HOST),
													port=sf.get_env_var(ENV.DB_PORT))

	# conn = psycopg2.connect(user=sf.get_env_var(ENV.DB_USER), 
	# 												password=sf.get_env_var(ENV.DB_PASS), 
	# 												host=sf.get_env_var(ENV.DB_HOST),
	# 												port=sf.get_env_var(ENV.DB_PORT))
	cur = conn.cursor()

	# conn.autocommit = True
	# db_string = "CREATE DATABASE " + sf.get_env_var(ENV.DB_NAME)
	# cur.execute(db_string)

	test_table = "test1"
	# Execute a command: this creates a new table
	cur.execute("CREATE TABLE " + test_table +  "(id serial PRIMARY KEY, num integer, data varchar);")
	conn.commit()
	# Pass data to fill a query placeholders and let Psycopg perform
	# the correct conversion (no more SQL injections!)
	cur.execute("INSERT INTO " + test_table + "(num, data) VALUES (%s, %s)", (100, "abc'def"))
	conn.commit()
	# Query the database and obtain data as Python objects
	cur.execute("SELECT * FROM " + test_table + ";")
	print(cur.fetchone())

	# Make the changes to the database persistent
	conn.commit()

	# Close communication with the database
	cur.close()
	conn.close()

if __name__ == "__main__":
	log.info(f"Started '__main__' of '{__file__:s}'")

	# create_table("lmfao", "id serial PRIMARY KEY, num integer, data varchar")
	# drop_table("lmfao")
	# for i in range(0, 100):
	# 	tx = f"(num, data) VALUES ({i*10}, 'nek random text {i * 10}')"
	# 	insert_into("lmfao", tx)
	# conn.commit()
	data = select_from("lmfao")

	print("All done")
	cur.close()
	conn.close()
	log.info(f"Finished '__main__' of '{__file__:s}'")