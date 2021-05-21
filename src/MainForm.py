from sys import hash_info
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

# Graphing needs
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.dates as mdates
import pandas as pd

log = sf.set_logging("MainForm")

### GLOBAL VARIABLES AND STUFF

# As PySimpleGUI does not support dynamic layouts out of the box
# we can use a combination of deep copying the layout and then
# recreating the window from scratch ...
w = None
refresh_window = True
w_size = (1680, 980)
w_pos = (150, 40)
col_listings_color = "#F9FBFD"
col_bg_2 = "#ebf0fa"
col_viewing_color = "#FFE4E1"
col_listings_color_back = "#EBEEF3"
color_accent_main = "#5079D3"
color_selected = "Slategray1"
color_deselected = col_listings_color
color_change_positive = "#4bd37b"
color_change_negative = "#d3574b"
font_family = 'Cascadia Code'
font_size = 14
font = (font_family, font_size)
graph_w = 100
graph_h = 50
plt.rcParams["font.family"] = font_family
plt.rcParams['font.size'] = font_size
can_auto_update = False
first_init = True

# Stores listings data where keys are crypto coin IDs and values are listings for each separate coin
listings_data = {}
last_update_at = "/"
collections = {} # Obtained from portfolios - keys are collection names values are dictionaries where each dictionary has coin ids for keys and quantity of said coin as values
timeseries = None
selected_coin_listing = {}
selected_coin_id = 1 # 1 = bitcoin ; 1027 = ethereum
coins_viewable = 20 # 20
listings_history = 4000 # 300

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

def db_get_portfolio_entries():
	user_id = user["id"]
	#entries = db.select_from(config.tablename_portfolios, conditions=f" WHERE user_id = '{user_id}' AND collection = '{collection}' ")
	entries = db.select_from(config.tablename_portfolios, conditions=f" WHERE user_id = '{user_id}' ")
	return entries

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
log.info("Logged in default user")

# Test portfolios
# db_create_table_portfolios()
# db_create_portfolio_entry(1, 42)
# db_create_portfolio_entry(1027, 8)
# portfolio_entries1 = db_get_portfolio_entries()
# collection = "my special collection"
# db_create_portfolio_entry(1027, 2)
# portfolio_entries2 = db_get_portfolio_entries()
# user = {}
# user["username"] = "john"
# user["id"] = 2
# db_create_portfolio_entry(1, 24)
# db_create_portfolio_entry(1027, 5)
# portfolio_entries3 = db_get_portfolio_entries()
# collection = "my very special collection"
# db_create_portfolio_entry(1027, 1)
# portfolio_entries4 = db_get_portfolio_entries()
# print("Tested portfolios")

# Get portfolio entries
def generate_collections():
	db_create_table_portfolios()
	global collection
	global collections
	collections = {}
	db_portfolio_entries = db_get_portfolio_entries()
	# Ensure there is always at least the default collection (even if it has 0 value)
	if len(db_portfolio_entries) == 0:
		db_create_portfolio_entry(1, 0)
		db_portfolio_entries = db_get_portfolio_entries()
	for entry in db_portfolio_entries:
		collection_name = entry[3]
		if not collection_name in collections:
			collections[collection_name] = {}
		collections[collection_name][entry[2]] = entry[4]
	if collection not in collections:
		if len(collections.keys()) > 0:
			collection = list(collections.keys())[0]
		else:
			collection = collection_default_name
	return collections

def update_holding():
	input_text = w.ReturnValuesDictionary["input_holding"]
	# Check if user input a number and update the db portfolios record else just reset to default input value
	try:
		input_val = float(input_text)
		# Create if it doesn't already exist
		db_create_portfolio_entry(selected_coin_id, 0)
		db.update_at(config.tablename_portfolios, "quantity=%s WHERE user_id=%s AND coin_id=%s AND collection=%s", [input_val, user["id"], selected_coin_id, collection])
		generate_collections()
		update_info()
	except Exception as e:
		w["input_holding"].update(w["input_holding"].DefaultText)

def remove_holding(coin_id):
	db.delete_from(config.tablename_portfolios, "user_id=%s AND coin_id=%s AND collection=%s", [user["id"], coin_id, collection])
	generate_collections()
	update_info()

# Generate collections and their coins and holdings quantities
collections = generate_collections()
log.info("Got collections from portfolios")

# VERY suboptimal but works for now
def generate_timeseries():
	listings_all = list(reversed(db.select_from("live_listings", nrows=listings_history, reversed=True)))
	global timeseries
	timeseries = {}
	counter = 0 
	for listing in listings_all:
		for coin in listing[2]["data"]:
			coin_id = coin["id"]
			if not coin_id in timeseries:
				timeseries[coin_id] = {}
				timeseries[coin_id]["timestamps"] = []
				timeseries[coin_id]["prices"] = []
			timeseries[coin_id]["timestamps"].append(datetime.datetime.strptime(coin["last_updated"], '%Y-%m-%dT%H:%M:%S.%fZ'))
			timeseries[coin_id]["prices"].append(coin["quote"]["EUR"]["price"])
		if counter >= listings_history: # limit when testing
			break
		counter += 1
	return timeseries

# Time series to OHLC conversions
# def timeseries_to_OHLC(timestamps, prices):
# 	df = pd.DataFrame({"Timestamps": timestamps, "Prices": prices})
# 	print(df)
# 	df.resample('5M').agg({'openbid': 'first', 
# 													'highbid': 'max', 
# 													'lowbid': 'min', 
# 													'closebid': 'last'})
# 	print(df)
	
# ether_timeseries = timeseries[1027]
# ohlc_test = timeseries_to_OHLC(ether_timeseries["timestamps"], ether_timeseries["prices"])
# print("Done generating OHLC from timeseries")

### Graphing

class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)

def draw_figure_w_toolbar(canvas, fig, canvas_toolbar):
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    if canvas_toolbar.children:
        for child in canvas_toolbar.winfo_children():
            child.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(fig, master=canvas)
    figure_canvas_agg.draw()
    toolbar = Toolbar(figure_canvas_agg, canvas_toolbar)
    toolbar.update()
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)

def draw_graph():
	if timeseries == None:
		return None
	plt.clf()
	plt.clf()
	plt.close()
	plt.figure(1)
	# fig = plt.gcf()
	fig, ax = plt.subplots()
	fig.patch.set_facecolor(col_listings_color)
	ax.set_facecolor(col_listings_color)
	DPI = fig.get_dpi()
	fig.set_size_inches(graph_w / float(DPI), graph_h / float(DPI))

	y = timeseries[selected_coin_id]["prices"]
	x = range(len(y))
	dates = timeseries[selected_coin_id]["timestamps"]

	# Prepare daily slices
	day_slices_timestamps = []
	day_slices_prices = []
	current_day = -1
	for price, timestamp in zip(y, dates):
		day = timestamp.day
		if day != current_day:
			current_day = day
			day_slices_prices.append([])
			day_slices_timestamps.append([])
		day_slices_prices[len(day_slices_prices) - 1].append(price)
		day_slices_timestamps[len(day_slices_timestamps) - 1].append(timestamp)

	# z = np.polyfit(x, y, 24)#5 * 4 * 3)#12*5 * 2) # Cetrtletje al pa meseci
	# z2 = np.polyfit(x, y, 0) # Povprecje
	# z3 = np.polyfit(x, y, 1) # Trend
	# p = np.poly1d(z)
	# p2 = np.poly1d(z2)
	# p3 = np.poly1d(z3)

	pri_opacity = 1.0
	sec_opacity = 1.0
	k = "Hmm"

	# pp = ax.plot(dates,p(x), label=(k if pri_opacity >= sec_opacity else ''), alpha=pri_opacity)
	# last_col = pp[-1].get_color()
	last_col = color_accent_main
	ax.plot(dates, y, last_col, label="yoo wtf", alpha=sec_opacity, linewidth=1.5) # Vsi podatki alpha=0.15
	# ax.plot(dates, p2(x))

	# Plot slices
	for prices, timestamps in zip(day_slices_prices, day_slices_timestamps):
		col = "#F2CD31" # same open and close price
		if prices[0] < prices[len(prices) - 1]:
			col = color_change_positive
		if prices[0] > prices[len(prices) - 1]:
			col = color_change_negative
		ax.plot(timestamps, prices, col, label="", alpha=sec_opacity, linewidth=2.0)

	# To je za debelo crto
	# ax.plot(dates, p3(x), last_col, linewidth=3.0)

	# Rotate and align the tick labels so they look better.
	fig.autofmt_xdate()
	ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')

	plt.title(listings_data[selected_coin_id]["name"])
	plt.xlabel("time")
	plt.ylabel('price')
	plt.grid()
	plt.subplots_adjust(left=0.085, bottom=None, right=0.97, top=0.95, wspace=None, hspace=None)
	draw_figure_w_toolbar(w['fig_cv'].TKCanvas, fig, w['controls_cv'].TKCanvas)

### End of Graphing

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
		color = color_change_positive
	if change_val < 0:
		color = color_change_negative
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

### GENERATE Live listings
def generate_live_listings():
	global last_update_at
	global listings
	global listings_data
	listings_data = {}
	dg_listings = dg.get_coinmarketcap_listings()
	db_listings = db.select_last("live_listings")
	listings = dg_listings["data"]
	for listing in listings:
		listings_data[listing["id"]] = listing
	last_update_at = db_listings[1]
	# Generate timeseries
	generate_timeseries()
	log.info("Got timeseries")


# Build main layout when the main window is being created
# This can be either be called at program start or when redrawing new layout
def build_main_layout():
	global font
	generate_live_listings()
	win_w = w_size[0] #px_to_char_w(w_size[0])
	win_h = w_size[1] #px_to_char_h(w_size[1])
	menubar_w = win_w
	menubar_h = 50
	col_listings_w = 580
	col_listings_h = win_h - menubar_h
	tracked_listings_table = []
	all_listings_table = []
	i = 0
	padd = 5
	for listing in listings:
		in_collection = is_in_collection(listing["id"])
		img_path = get_image_path(listing["id"])
		ltext = f"{listing['name']}\n{listing['quote']['EUR']['price']:.2f} €"
		view_button = sg.Button(button_text="🔍", button_color="Slateblue1", pad=(padd, padd), size=(2, 1), font=(font_family, 12), key=f"browse_coin-{listing['id']}")
		add_button_text = ""
		add_button_color = ()
		if in_collection:
			add_button_text = "➖"
			add_button_color = color_change_negative
		else:
			add_button_text = "➕"
			add_button_color = color_change_positive
		add_button = sg.Button(button_text=add_button_text, button_color=add_button_color, pad=(padd, padd), size=(2,1), font=(font_family, 12), key=f"add_button-{listing['id']}")
		# crypto_img = sg.Image(filename="res/prog/missing_crypto.png", size=(64, 64), pad=(padd, padd), background_color=col_listings_color)
		crypto_img = sg.Image(filename=img_path, size=(64, 64), pad=(padd, padd), background_color=col_listings_color)
		crypto_text = sg.Text(ltext, background_color=col_listings_color, pad=(padd * 2, padd), size=(20, None), enable_events=True, key=f"crypto_text-{listing['id']}")
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
					], pad=(padd * 2,0), background_color=col_listings_color
				)
			]], pad=(padd, padd), background_color=col_listings_color)]
		)
		i += 1
		if i >= coins_viewable:
			break

	listings_topbar_layout = [
			[
				sg.Text('Live listings', background_color=col_listings_color, key="listings_title", size=(28,2), pad=(padd, padd)), 
				sg.Check("Auto update", default=can_auto_update, key="auto_update", background_color=col_listings_color, pad=(padd, padd)),
				sg.Button("Update", key="update_listings", pad=(padd, padd))
			],
			[
				sg.Combo(values=["ena", "dve"], size=(30,3), pad=(padd, padd), auto_size_text=False, background_color=col_listings_color, text_color=color_accent_main, readonly=True, change_submits=True, enable_events=True, key="collections_dropdown")
			],
		]

	listings_topbar = sg.Column(listings_topbar_layout, pad=(0, 0), element_justification='center', key="listings_topbar", size=(col_listings_w, 150), background_color=col_listings_color, justification="center")

	listings_table_layout = [
		[sg.Text(f"Portfolio ({len(collections[collection].keys())})", pad=(padd + 10, padd + 10), font=(font_family, 20), background_color=col_bg_2, key="portfolio_text")],
		[sg.Column(tracked_listings_table, background_color=col_bg_2)],
		[sg.Text(f"All crypto ({len(all_listings_table)})", pad=(padd + 10, padd + 10), font=(font_family, 20), background_color=col_bg_2)],
		[sg.Column(all_listings_table, background_color=col_bg_2)]
	]

	col_listings_layout = [
		[
			listings_topbar
		], 
		[
			# 18 needed to subtract from sizes to adjust for the scrollbars (there seems to be a bug in the pysimplegui box model)
			# Also there is 1px of top,left offest even if setting all padding to (0, 0)
			sg.Column(listings_table_layout, pad=(0, 0), element_justification='l', key="listings_list", size=(col_listings_w - 18, col_listings_h-listings_topbar.Size[1] - 18), scrollable=True, background_color=col_bg_2)
		]
	]


	col_viewing_w = win_w - col_listings_w
	col_viewing_h = col_listings_h
	details_h = 300

	controls_h = 50
	global graph_w
	global graph_h
	graph_w = col_viewing_w
	graph_h = col_viewing_h - details_h - controls_h
	graphing_layout = [
			[
				sg.Column(
				layout=[
					[sg.Canvas(key='fig_cv',
											# it's important that you set this size
											size=(graph_w, graph_h),
											background_color=col_listings_color
										)]
				],
				background_color=col_listings_color,
				pad=(0, 0), size=(graph_w, graph_h))
			],
			[sg.Canvas(key='controls_cv', background_color=col_listings_color)],
		]

	# graphing_layout = [
  #   [sg.Text('Graph: y=sin(x)')],
  #   [sg.Button('Plot'), sg.Button('Exit')],
  #   [sg.Text('Controls:')],
  #   [sg.Canvas(key='controls_cv')],
  #   [sg.Text('Figure:')],
  #   [sg.Column(
	# 		layout=[
	# 			[sg.Canvas(key='fig_cv',
	# 									# it's important that you set this size
	# 									size=(400 * 2, 400)
	# 								)]
	# 		],
	# 		background_color='#DAE0E6',
	# 		pad=(0, 0)
	# )],
  #   [sg.Button('Alive?')]
	# ]

	details_layout = [
		[
			sg.Text("Holding quantity:", pad=(padd, padd), background_color=col_listings_color),
			sg.Input(default_text="0", size=(10, 1), justification="l", pad=(padd, padd), background_color=col_listings_color, text_color=color_accent_main, key="input_holding"),
			sg.Text(f"Value: 0 €", pad=(padd, padd), background_color=col_listings_color, key="holding_value", size=(30, 1)),
			sg.Button("Update", size=(8, 1), pad=(padd * 2, padd), button_color=(col_listings_color, color_accent_main), key="update_holding"),
			sg.Button("Add", size=(8, 1), pad=(padd * 2, padd), button_color=(col_listings_color, color_accent_main), key="addremove_button_info")
		],
		[
			sg.Text("Collection: ", size=(30, 1), pad=(padd, padd), background_color=col_listings_color, key="text_collection")
		]
	]

	col_viewing_layout = [
		[
			sg.Column(graphing_layout, background_color=col_listings_color, size=(col_viewing_w, col_viewing_h - details_h))
		],
		[
			sg.Column(details_layout, background_color=col_listings_color, size=(col_viewing_w, details_h), pad=(padd*2, padd*2))
		]
	]
	# col_graphing=[[sg.Text('Graphing', background_color='green', size=(1,1))]]
	
	menubar_layout = [
		[
			sg.Column([
				[
					sg.Button("Login", button_color=(color_accent_main, col_listings_color), border_width=0, key="login", auto_size_button=True, pad=(padd, padd)),
					sg.Text(f"👤: {user['username']}", key="username", text_color=col_listings_color, background_color=color_accent_main, auto_size_text=True, justification="r", pad=(padd * 2, padd))
				]
				], background_color=color_accent_main, pad=(padd, None), vertical_alignment="c", justification="r", element_justification="r")
		]
	]

	menubar = sg.Column(menubar_layout, background_color=color_accent_main, size=(menubar_w, menubar_h), vertical_alignment="c", justification="r", element_justification="r")

	main_layout = [
		[
			menubar
		],
		[
			sg.Column(col_listings_layout, element_justification='c', key="listings", pad=(0,0), size=(col_listings_w, col_listings_h), background_color=col_listings_color, scrollable=False),
			sg.Column(col_viewing_layout, element_justification='c', key="viewing", pad=(0,0), size=(col_viewing_w, col_viewing_h), background_color=col_listings_color)
		]
	]

	return main_layout

def init_window(name="SimpleCryptoWatch"):
	global font
	global w
	global w_size
	global w_pos

	generate_collections()

	font=font
	temp_w = sg.Window(f"{name} - Initializing", [[sg.Text("Initializing main window\nPlease wait ✨", justification="c", background_color=col_listings_color, text_color="black")]], font=font, return_keyboard_events=True, finalize=True, background_color=col_listings_color, margins=(0, 0), element_padding=None)
	temp_w.read(timeout=0.001)
	temp_w.BringToFront()

	sg.theme("Material 1")
	main_layout = build_main_layout()
	w = sg.Window(name, 
		main_layout, 
		return_keyboard_events=True, 
		finalize=True, font=font, 
		resizable=True, 
		element_padding=(0, 0), 
		margins=(0, 0), 
		background_color=col_listings_color, 
		element_justification="c", 
		location=w_pos)
	
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
	global first_init
	if first_init:
		first_init = False
		w.BringToFront()
	temp_w.close()
	update_info()
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

def update_info(coin_id=None):
	global selected_coin_id
	global selected_coin_listing
	# if coin_id == None:
	
	# Deselect previously selected
	w[f"crypto_text-{selected_coin_id}"].update(background_color=color_deselected)
	if coin_id != None:
		selected_coin_id = coin_id
	# Select current
	w[f"crypto_text-{selected_coin_id}"].update(background_color=color_selected)
	selected_coin_listing = listings_data[selected_coin_id]
	# Update info
	holding_val = 0
	if is_in_collection(selected_coin_id):
		holding_val = float(collections[collection][selected_coin_id])
	input_holding = w.FindElement('input_holding')
	# Why can't I update these basic element properties dynamically... so limiting
	# input_holding.Update(size=(min(8, len(str(holding_val)) + 3), 1))
	input_holding.Update(f"{str(holding_val)}")
	el_holding_value = w["holding_value"]
	price = selected_coin_listing['quote']['EUR']['price']
	el_holding_value.update(f"Value: {(holding_val * price):.2f} €")
	# Update add remove button in details
	addremove_button = w["addremove_button_info"]
	addremove_button_text = ""
	addremove_button_color = None
	if is_in_collection(selected_coin_id):
		addremove_button_text = "Remove"
		addremove_button_color = color_change_negative
	else:
		addremove_button_text = "Add"
		addremove_button_color = color_change_positive
	addremove_button.update(text=addremove_button_text)
	addremove_button.update(button_color=addremove_button_color)
	# Update collection text
	w["text_collection"].update(f"Collection: {collection}")
	# Update collections dropdown
	w["collections_dropdown"].update(values=list(collections.keys()))
	w["collections_dropdown"].update(value=collection)
	# Update portfolio text
	w["portfolio_text"].update(f"Portfolio ({len(collections[collection].keys())})")
	# Update graph
	draw_graph()

def get_coin_id(event):
	return int(event[event.rindex("-")+1:])

def browse_coin(coin_id):
	slug = listings_data[coin_id]["slug"]
	url = f"https://coinmarketcap.com/currencies/{slug}/"
	os.startfile(url)

def add_coin(coin_id, quantity=0):
	db_create_portfolio_entry(coin_id, quantity)
	generate_collections()
	update_info()

def remove_coin(coin_id):
	# TODO implement db_remove_portfolio_entry
	remove_holding(coin_id)
	generate_collections()
	update_info()

def addremove_coin(coin_id):
	if is_in_collection(coin_id):
		remove_coin(coin_id)
	else:
		add_coin(coin_id)
	# Then check again and update the + - button
	if is_in_collection(coin_id):
		w[f"add_button-{coin_id}"].update(text="➖")
		w[f"add_button-{coin_id}"].update(button_color=color_change_negative)
	else:
		w[f"add_button-{coin_id}"].update(text="➕")
		w[f"add_button-{coin_id}"].update(button_color=color_change_positive)

def is_in_collection(coin_id):
	return collection in collections and coin_id in collections[collection]

def switch_collection(collection_name):
	global collection
	collection = collection_name
	generate_collections()
	update_info()

def main_loop():
	global refresh_window
	refresh_window = False
	w = init_window()

	i = 0
	# Process window 'events'
	while True:
		if refresh_window:
			break
		event, values = w.Read(timeout=16, timeout_key="w_timeout")
		
		# Do stuff even if there is nothing to be read
		lt = w.FindElement("listings_title")
		time_now = datetime.datetime.now().astimezone()
		to_be_updated_at = last_update_at + datetime.timedelta(seconds=config.interval_coinmarketcap)
		# + 5 to leave some headroom in case the data is not yet in db
		time_till_next_update_s = (to_be_updated_at - time_now).total_seconds() + 5
		if time_till_next_update_s <= 0 and w.ReturnValuesDictionary["auto_update"] == True:
			# generate_live_listings()
			# update_info()
			refresh_window = True
			continue
		lt.update(f"Time: {time_now.strftime('%d.%m.%Y %H:%M:%S')}\nNext update in: {time_till_next_update_s:.1f}s")
		
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
			coin_id = get_coin_id(event)
			if coin_id != selected_coin_id:
				update_info(coin_id)

		# Add / remove coin from collection
		if "add_button" in event:
			addremove_coin(get_coin_id(event))

		if "addremove_button_info" in event:
			addremove_coin(selected_coin_id)

		if "browse_coin-" in event:
			browse_coin(get_coin_id(event))

		if "collections_dropdown" in event:
			dropdown_val = w.ReturnValuesDictionary["collections_dropdown"]
			if dropdown_val != collection:
				switch_collection(dropdown_val)

		if event == "sizemoved":
			handle_window_sizemoved()

		# if event == "Button":
		# 	MainFormLayout.main_layout.append([sg.Text('This is a very basic PySimpleGUI layout')])
		# 	refresh_window = True

		if "update_holding" in event:
			update_holding()

		if "update_listings" in event:
			# generate_live_listings()
			# update_info()
			refresh_window = True
			continue

		# Graphing
		if event is 'Plot':
			draw_graph()


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