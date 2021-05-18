import PySimpleGUI as sg
# import MainFormLayout
import os

from PySimpleGUI.PySimpleGUI import Column
import DatabaseConnector as db
import SupportFunctions as sf
import DataGrabber as dg
import math
import urllib.request
import datetime
import time
import config
import hashlib, uuid

log = sf.set_logging("MainForm")

### GLOBAL VARIABLES AND STUFF

# As PySimpleGUI does not support dynamic layouts out of the box
# we can use a combination of deep copying the layout and then
# recreating the window from scratch ...
w = None
refresh_window = True
w_size = (1480, 820)
w_pos = (150, 40)
selected_key = None
col_listings_color = "#F9FBFD"
col_viewing_color = "#FFE4E1"
col_listings_color_back = "#EBEEF3"
color_selected = "Slategray1"
color_deselected = col_listings_color
font_family = 'Cascadia Code'
font_size = 14
font = (font_family, font_size)

# DB
# Default user ensures out of the box functionality but should not be used if you plan on storing portfolio data
user_default_username = "DEFAULT"
user_default_pass = "12345"
user = None # Stores the user object
collection_default_name = "Default collection"
collection = collection_default_name # for now a collection is just a name - later we would ideally make it into its own table with (id primary int, owner_id int (user), name text, ... UNIQUE(owner_id, name) )

### END OF GLOBAL VARIABLES


### DB SPECIFIC STUFF (would ideally be separate from frontend)

# USERS

def db_create_table_users():
	# Bad design from a security standpoint - password hashes and salts should (ideally) be stores on a separate machine
	db.create_table(config.tablename_users, "id serial PRIMARY KEY, username text UNIQUE, passhash text, salt text")

def db_create_user(username, password):
	salt = uuid.uuid4().hex
	hashed_password = hashlib.sha512(password.encode('utf-8') + salt.encode('utf-8')).hexdigest()
	db.insert_into(config.tablename_users, '(username, passhash, salt) values (%s, %s, %s)', [username, hashed_password, salt])

def db_read_users():
	return db.select_from(config.tablename_users)

def db_login_user(username, password):
	user = None
	users = db.to_dict(db_read_users(), ["id", "username", "passhash", "salt"])
	# Could be optimized by creating a better select query but it works for now
	for user in users:
		if user["username"] == username:
			if user["passhash"] == hashlib.sha512(password.encode('utf-8') + user["salt"].encode('utf-8')).hexdigest():
				user_filtered = user
				# Remove passhash and salt so they are not stored in RAM long-term
				user_filtered.pop("passhash", None)
				user_filtered.pop("salt", None)
				return user_filtered
			else:
				# TODO throw up a popup or something - "correct username but wrong"
				return -1 # found a user but the passwords did not match
	return -2 # didn't find the user - gets the info to maybe create said user

# COLLECTIONS - for now we will use only collection name inside of PORTFOLIOS

# PORTFOLIOS

def db_create_table_portfolios():
	db.create_table(config.tablename_portfolios, "id serial PRIMARY KEY, user_id INTEGER, coin_id INTEGER, collection TEXT, quantity DECIMAL, UNIQUE(user_id, coin_id, collection)")

def db_create_portfolio_entry(coin_id, quantity):
	user_id = user["id"]
	db.insert_into(config.tablename_portfolios, '(user_id, coin_id, collection, quantity) values (%s, %s, %s, %s)', [user_id, coin_id, collection, quantity])

### END OF DB SPECIFIC STUFF

# A little janky but should do for proof of work
def login_user(username, password):
	db_create_table_users()
	global user
	userlogin = db_login_user(username, password)
	if userlogin == -2:
		db_create_user(username, password)
		userlogin = db_login_user(username, password)
	user = userlogin
	return user
	
# Login the DEFAULT user
user = login_user(user_default_username, user_default_pass)

# Test portfolios
# db_create_table_portfolios()
# db_create_portfolio_entry(1, 42)

def set_size():
	None

def px_to_char_w(px):
	# 13px per char width
	pxu = 11.0
	return math.floor(float(px) / float(pxu))

def px_to_char_h(px):
	# 24px per char height
	pxu = 22
	return math.floor(float(px) / float(pxu))

def get_image_path(id):
	qstr = f"https://s2.coinmarketcap.com/static/img/coins/64x64/{id}.png"
	fname = f"res/web/{id}.png"
	if not os.path.isdir("res/web/"):
		os.makedirs("res/web/")
	if not os.path.exists(fname):
		urllib.request.urlretrieve(qstr, fname)
	return fname

def get_change_color(change_val):
	color = "black"
	if change_val > 0:
		color = "#4bd37b"
	if change_val < 0:
		color = "#d3574b"
	return color

def get_change_text(change_val):
	if change_val == 0:
		return "-||-"
	else:
		return f"{change_val:3.2f}%"
		# if change_val > 0:
		# 	return f"+ {change_val}%"
		# else:
		# 	return f"- {change_val}%"

# Build main layout when the main window is being created
# This can be either be called at program start or when redrawing new layout
def build_main_layout():
	global font
	### GENERATE Live listings
	dg_listings = dg.get_coinmarketcap_listings()
	db_listings = db.select_last("live_listings")
	listings = db_listings[2]["data"]
	win_w = w_size[0] #px_to_char_w(w_size[0])
	win_h = w_size[1] #px_to_char_h(w_size[1])
	menubar_w = win_w
	menubar_h = 50
	col_listings_w = 550
	col_listings_h = win_h - menubar_h
	tracked_listings_table = []
	all_listings_table = []
	i = 0


	padd = 5
	for listing in listings:
		img_path = get_image_path(listing["id"])
		ltext = f"{listing['name']}\n{listing['quote']['EUR']['price']:.2f} €"
		view_button = sg.Button(button_text="🔍", button_color="Slateblue1", pad=(padd, padd), size=(2, 1), font=(font_family, 12))
		add_button = sg.Button(button_text="➕", button_color=get_change_color(1), pad=(padd, padd), size=(2,1), font=(font_family, 12))
		# crypto_img = sg.Image(filename="res/prog/missing_crypto.png", size=(64, 64), pad=(padd, padd), background_color=col_listings_color)
		crypto_img = sg.Image(filename=img_path, size=(64, 64), pad=(padd, padd), background_color=col_listings_color)
		crypto_text = sg.Text(ltext, background_color=col_listings_color, pad=(padd, padd), size=(20, None), enable_events=True, key=f"crypto_text-{listing['id']}")
		t24h = sg.Text("24h:", justification="r", size=(4, None), pad=(padd, padd), background_color=col_listings_color)
		t7d = sg.Text("7d:", justification="r", size=(4, None), pad=(padd, padd), background_color=col_listings_color)
		change_24h = listing["quote"]["EUR"]["percent_change_24h"]
		change_7d = listing["quote"]["EUR"]["percent_change_7d"]
		text_delta_24h = sg.Text(get_change_text(change_24h), background_color=col_listings_color, pad=(padd, padd), size=(8, None), text_color=get_change_color(change_24h), justification="r")
		text_delta_7d = sg.Text(get_change_text(change_7d), background_color=col_listings_color, pad=(padd, padd), size=(8, None), text_color=get_change_color(change_7d), justification="r")
		all_listings_table.append([sg.Column(
			[[
				sg.Column(
					[
						[view_button],
						[add_button]
					], pad=(10, 0), background_color=col_listings_color
				),
				crypto_img,
				crypto_text,
				sg.Column(
					[
						[t24h],
						[t7d]
					], pad=(0,0), background_color=col_listings_color
				),
				sg.Column(
					[
						[text_delta_24h],
						[text_delta_7d]
					], pad=(0,0), background_color=col_listings_color
				)
			]], pad=(padd, padd), background_color=col_listings_color)]
		)
		i += 1
		if i >= 20:
			break

	listings_topbar_layout = [
			[sg.Text('Live listings', background_color='Slategray1', key="listings_title", size=(30,3)), sg.Button("+", key="add_text"), sg.Button("-", key="remove_text")],
			[sg.Column([[sg.Column([[sg.Text("yooo")]], key="yooo")]], key="topbar_texts")]
		]

	listings_topbar = sg.Column(listings_topbar_layout, pad=(0, 0), element_justification='center', key="listings_topbar", size=(col_listings_w, 150), background_color=col_listings_color, justification="center")

	listings_table_layout = [
		[sg.Text(f"Portfolio ({len(tracked_listings_table)})", pad=(padd + 10, padd + 10), font=(font_family, 20), background_color=col_listings_color_back)],
		[sg.Column(tracked_listings_table, background_color=col_listings_color_back)],
		[sg.Text(f"All crypto ({len(all_listings_table)})", pad=(padd + 10, padd + 10), font=(font_family, 20), background_color=col_listings_color_back)],
		[sg.Column(all_listings_table, background_color=col_listings_color_back)]
	]

	col_listings_layout = [
		[
			listings_topbar
		], 
		[
			# 18 needed to subtract from sizes to adjust for the scrollbars (there seems to be a bug in the pysimplegui box model)
			# Also there is 1px of top,left offest even if setting all padding to (0, 0)
			sg.Column(listings_table_layout, pad=(0, 0), element_justification='l', key="listings_list", size=(col_listings_w - 18, col_listings_h-listings_topbar.Size[1] - 18), scrollable=True, background_color="#EBEEF3")
		]
	]


	col_viewing_w = win_w - col_listings_w
	col_viewing_h = col_listings_h
	details_h = 300

	col_viewing_layout = [
		[
			sg.Column([[sg.Text("Graphing")]], background_color="lime", size=(col_viewing_w, col_viewing_h - details_h))
		],
		[
			sg.Column([[sg.Text("Details")]], background_color="orange", size=(col_viewing_w, details_h))
		]
	]
	# col_graphing=[[sg.Text('Graphing', background_color='green', size=(1,1))]]

	menubar = sg.Column([[sg.Text("Menu test")]], background_color="violet", size=(menubar_w, menubar_h))

	main_layout = [
		[
			menubar
		],
		[
			sg.Column(col_listings_layout, element_justification='c', key="listings", pad=(0,0), size=(col_listings_w, col_listings_h), background_color=col_listings_color, scrollable=False),
			sg.Column(col_viewing_layout, element_justification='c', key="viewing", pad=(0,0), size=(col_viewing_w, col_viewing_h), background_color=col_viewing_color)
		]
	]

	return main_layout

def init_window(name="SimpleCryptoWatch"):
	global font
	global w
	global w_size
	global w_pos
	font=font
	temp_w = sg.Window(f"{name} - Initializing", [[sg.Text("Initializing main window\nPlease wait ✨", justification="c", background_color="white", text_color="black")]], font=font, return_keyboard_events=True, finalize=True, background_color="white", margins=(0, 0), element_padding=None)
	temp_w.read(timeout=0.001)
	temp_w.BringToFront()

	sg.theme("Material 1")
	main_layout = build_main_layout()
	if w_pos:
		w = sg.Window(name, main_layout, return_keyboard_events=True, finalize=True, font=font, resizable=True, element_padding=(0, 0), margins=(0, 0), location=w_pos)
	else:
		w = sg.Window(name, main_layout, return_keyboard_events=True, finalize=True, font=font, resizable=True, element_padding=(0, 0), margins=(0, 0))
	if w_size:
		w.size = w_size
	else:
		w_size = w.size
	if w_pos:
		None # TODO set window location
	else:
		w_pos = w.current_location()
	
	# Shows as program icon but not in taskbar
	w.SetIcon(os.path.abspath("logo.ico"))
	# Resize event
	w.bind('<Configure>', "sizemoved")
	w.BringToFront()
	temp_w.close()
	return w

# Handles moving and resizing of the window - used for later redrawing
def handle_window_sizemoved():
	global w_size
	global w_pos
	global refresh_window
	if w_size[0] != w.size[0] or w_size[1] != w.size[1]:
		w_size = w.size
		refresh_window = True
		# TODO call redraw window layout accordingly
	cur_loc = w.current_location()
	if w_pos[0] != cur_loc[0] or w_pos[1] != cur_loc[1]:
		w_pos = cur_loc

def main_loop():
	global refresh_window
	refresh_window = False
	w = init_window()

	i = 0
	# Process window 'events'
	while True:
		event, values = w.Read(timeout=16, timeout_key="w_timeout")
		
		# Do stuff even if there is nothing to be read
		lt = w.FindElement("listings_title")
		lt.update(f"Time: {str(datetime.datetime.now()) } OK")
		
		# If the user closes the window - end it all
		if event in (sg.WIN_CLOSED, 'Exit'):
			break

		# Check if you even have an event
		if not event:
			continue

		# Just skip window specific updates if nothing is read
		if "w_timeout" in event:
			continue

		# From here on out update window stuff
		#
		#
		#
		# From here on out update window stuff

		# Print values - for debug
		print(event, values)

		if "add_text" in event:
			w.extend_layout(w["topbar_texts"], [[sg.Text("yoooo")]])
			a = 0
			# w["topbar_texts"].update(layout.append())
		
		if "remove_text" in event:
			w["yooo"].update(visible=False)
			w.refresh()
			# Hide element

		# Check if a specific row in crypto listings has been clicked to be selected for detailed viewing
		if "crypto_text" in event:
			global selected_key
			if selected_key != event:
				w[event].update(background_color=color_selected)
				if selected_key != None:
					w[selected_key].update(background_color=color_deselected)
				selected_key = event

		if event == "sizemoved":
			handle_window_sizemoved()

		# if event == "Button":
		# 	MainFormLayout.main_layout.append([sg.Text('This is a very basic PySimpleGUI layout')])
		# 	refresh_window = True


		if event == '-B1-':
			w.extend_layout(w['-COL1-'], [[sg.T('A New Input Line'), sg.I(key=f'-IN-{i}-')]])
			i += 1
		if event == '-B2-':
			w.extend_layout(w, [[sg.T('A New Input Line'), sg.I(key=f'-IN-{i}-')]])
			i += 1

		# Used for "dynamic layouts"
		if refresh_window:
			break

		# To reduce system strain
		# time.sleep(0.01)
	log.info("Closing window in main loop")
	w.close()

if __name__ == "__main__":
	# A way to fake layout updates
	while refresh_window:
		refresh_window = False
		log.info("Calling main loop")
		main_loop()