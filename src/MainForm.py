import PySimpleGUI as sg
# import MainFormLayout
import copy
import os
import DatabaseConnector as db
import SupportFunctions as sf
import DataGrabber as dg
import math
import requests
import urllib.request
import datetime
import time

sf.set_logging("MainForm")

# As PySimpleGUI does not support dynamic layouts out of the box
# we can use a combination of deep copying the layout and then
# recreating the window from scratch ...
w = None
refresh_window = True
w_size = (1480, 820)
w_pos = (150, 40)

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

def build_main_layout():
	### GENERATE Live listings
	dg_listings = dg.get_coinmarketcap_listings()
	db_listings = db.select_last("live_listings")
	listings = db_listings[2]["data"]
	win_w = w_size[0] #px_to_char_w(w_size[0])
	win_h = w_size[1] #px_to_char_h(w_size[1])
	col_listings_w = 550
	col_listings_h = win_h
	listings_table = []
	i = 0
	col_listings_color = "#F9FBFD"

	padd = 5
	for listing in listings:
		img_path = get_image_path(listing["id"])
		ltext = f"{listing['name']}\nPrice: {listing['quote']['EUR']['price']:.2f} €"
		view_button = sg.Button(button_text="🔍", button_color="Slateblue1", pad=(padd+10, padd))
		# crypto_img = sg.Image(filename="res/prog/missing_crypto.png", size=(64, 64), pad=(padd, padd), background_color=col_listings_color)
		crypto_img = sg.Image(filename=img_path, size=(64, 64), pad=(padd, padd), background_color=col_listings_color)
		crypto_text = sg.Text(ltext, background_color=col_listings_color, pad=(padd, padd), size=(20, None))
		t24h = sg.Text("24h:", justification="r", size=(4, None), pad=(padd, padd), background_color=col_listings_color)
		t7d = sg.Text("7d:", justification="r", size=(4, None), pad=(padd, padd), background_color=col_listings_color)
		change_24h = listing["quote"]["EUR"]["percent_change_24h"]
		change_7d = listing["quote"]["EUR"]["percent_change_7d"]
		text_delta_24h = sg.Text(get_change_text(change_24h), background_color=col_listings_color, pad=(padd, padd), size=(8, None), text_color=get_change_color(change_24h), justification="r")
		text_delta_7d = sg.Text(get_change_text(change_7d), background_color=col_listings_color, pad=(padd, padd), size=(8, None), text_color=get_change_color(change_7d), justification="r")
		listings_table.append(
			[
				view_button,
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
			]
		)
		i += 1
		# if i >= 5:
		# 	break

	listings_topbar = sg.Column(
		[
			[sg.Text('Live listings', background_color='Slategray1', key="listings_title", size=(30,3))]
		], 
		pad=(0, 0), element_justification='l', key="listings_topbar", size=(col_listings_w, 150), background_color=col_listings_color)

	col_listings=[
		[
			listings_topbar
		], 
		[
			sg.Column(listings_table, pad=(0, 0), element_justification='l', key="listings_list", size=(col_listings_w, col_listings_h-listings_topbar.Size[1]), scrollable=True, background_color=col_listings_color)
		]
	]


	col_graphing_w = win_w - col_listings_w
	col_graphing_h = col_listings_h
	col_graphing=[[sg.Text('Graphing', background_color='Slategray1')]]
	# col_graphing=[[sg.Text('Graphing', background_color='green', size=(1,1))]]

	main_layout = [
		[
			sg.Column(col_listings, element_justification='l', key="listings", pad=(0,0), size=(col_listings_w, col_listings_h), background_color=col_listings_color),
			sg.Column(col_graphing, element_justification='c', key="graphing", pad=(0,0), size=(col_graphing_w, col_graphing_h), background_color="misty rose"),
		]
	]

	# main_layout = [
	# 	listings_table,
	# 	[
	# 		[sg.Text('Thi is a very basic PySimpleGUI layout')],
	# 		[sg.Input()],
	# 		[sg.Button('Button'), sg.Button('Exit')]
	# 	]
	# ]

	return main_layout

def init_window(name="SimpleCryptoWatch"):
	global w
	global w_size
	global w_pos
	sg.theme("Material 1")
	main_layout = build_main_layout()
	if w_pos:
		w = sg.Window(name, main_layout, return_keyboard_events=True, finalize=True, font=('Cascadia Code', 14), resizable=True, element_padding=(0, 0), margins=(0, 0), location=w_pos)
	else:
		w = sg.Window(name, main_layout, return_keyboard_events=True, finalize=True, font=('Cascadia Code', 14), resizable=True, element_padding=(0, 0), margins=(0, 0))
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
		event, values = w._ReadNonBlocking()
		# Do stuff even if there is nothing to be read
		lt = w.FindElement("listings_title")
		lt.update(f"Time: {str(datetime.datetime.now()) } OK")
		if event or values:
			print(event, values)


			
			#datetime.datetime.now()

			# if event == sg.WINDOW_CLOSED:
			# 	break

			if event == "sizemoved":
				handle_window_sizemoved()

			# if event == "Button":
			# 	MainFormLayout.main_layout.append([sg.Text('This is a very basic PySimpleGUI layout')])
			# 	refresh_window = True

			if event in (sg.WIN_CLOSED, 'Exit'):
				break
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
		time.sleep(0.01)
	w.close()

if __name__ == "__main__":
	# A way to fake layout updates
	while refresh_window:
		refresh_window = False
		main_loop()