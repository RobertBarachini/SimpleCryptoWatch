# Handles DB connections and CRUD operations

# Handle on exit
import atexit
def exit_handler():
	try:
		log.info("In exit handler...closing cursor and connection")
		cur.close()
		conn.close()
		log.info("Closed cursor and connection - exiting")
	except Exception as e:
		log.error("Error occured when calling exit handler")
		log.error(e)
atexit.register(exit_handler)

from configparser import Error
import SupportFunctions as sf
log = sf.set_logging("DatabaseConnector")

import sys
for arg in sys.argv:
	log.info(f"arg: '{arg}'")


import os
log.info(f"CWD: '{os.getcwd()}'")

log.info("importing ENV")
import ENV
log.info("importing psycopg2")
import psycopg2
log.info("importing psycopg2 extras")
from psycopg2.extras import Json, DictCursor
import json
# import logging as log
import config
import time
import datetime

conn = None
cur = None

def to_dict(rows, colnames):
	if len(rows) == 0:
		return rows
	if len(rows[0]) != len(colnames):
		raise ValueError("Number of columns in a row doesn't match the number of columns in colnames")
	res = []
	for row in rows:
		rown = {}
		for index, name in zip(range(0, len(colnames)), colnames):
			rown[name] = row[index]
		res.append(rown)
	return res

# a = to_dict([[1, "b", "lmfao"], [2, "c", "lmoa"]], ["id", "name", "neki"])
# b = to_dict([[1, "b", "lmfao"], [2, "c", "lmoa"]], ["id", "name", "neki", "smh"])
# yo = 0

def init_conn(database, user, password, host, port, can_create=True):
	global conn
	global cur
	try:
		conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
		cur = conn.cursor()
	except Exception as e:
		log.error(e)
		# If connection was established but the database does not exist we can try to create it and retry
		# otherwise throw an exception
		if can_create and "does not exist" in str(e):
			create_db(database, user, password, host, port)
			# Retry connection
			init_conn(database, user, password, host, port, can_create=False)
		else:
			log.error(e)
			raise e
	return conn, cur
	

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

# Init DB connection
log.info("Initiating DB connection.")
init_conn(database=sf.get_env_var(ENV.DB_NAME), 
					user=sf.get_env_var(ENV.DB_USER), 
					password=sf.get_env_var(ENV.DB_PASS), 
					host=sf.get_env_var(ENV.DB_HOST),
					port=sf.get_env_var(ENV.DB_PORT))
log.info("Initiated DB connection.")

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

def insert_into(name, tx, data=None, auto_commit=True):
	tx = f"INSERT INTO {name} {tx};"
	try:
		log.info(f"Inserting into table '{name}' tx={tx}.")
		cur.execute(tx, data)
		if auto_commit:
			conn.commit()
	except Exception as e:
		log.error(e)
		log.error(f"Tx: {tx} ; Data: {data}")
		rollback()

def select_first(name):
	return select_from(name, nrows=1)

def select_last(name):
	return select_from(name, nrows=1, reversed=True)

def select_from(name, nrows=-1, reversed=False):
	tx = f"SELECT * FROM {name}{'' if not reversed else ' ORDER BY id DESC'};"
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