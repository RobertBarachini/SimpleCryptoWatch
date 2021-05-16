import PySimpleGUI as sg
# import MainFormLayout
import copy
import os
import DatabaseConnector as db
import SupportFunctions as sf
import math

sf.set_logging("MainForm")

# As PySimpleGUI does not support dynamic layouts out of the box
# we can use a combination of deep copying the layout and then
# recreating the window from scratch ...
w = None
refresh_window = True
w_size = (1280, 720)
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

def build_main_layout():
	### GENERATE Live listings
	db_listings = db.select_last("live_listings")
	listings = db_listings[2]["data"]
	win_w = w_size[0] #px_to_char_w(w_size[0])
	win_h = w_size[1] #px_to_char_h(w_size[1])
	col_listings_w = 400
	col_listings_h = win_h
	listings_table = []
	i = 0

	for listing in listings:
		ltext = f"{listing['name']} ; Price: {listing['quote']['EUR']['price']:.2f} €"
		listings_table.append([sg.Text(ltext, background_color="Slategray1", pad=(5,5))])
		i += 1
		# if i >= 5:
		# 	break

	col_listings=[
		[
			sg.Text('Live listings', background_color='Slategray1')
		], 
		listings_table
	]


	col_graphing_w = win_w - col_listings_w
	col_graphing_h = col_listings_h
	col_graphing=[[sg.Text('Graphing', background_color='Slategray1')]]
	# col_graphing=[[sg.Text('Graphing', background_color='green', size=(1,1))]]

	main_layout = [
		[
			sg.Column(listings_table, element_justification='l', key="listings", size=(col_listings_w, col_listings_h), scrollable=True, background_color="floral white"),
			sg.Column(col_graphing, element_justification='c', key="graphing", size=(col_graphing_w, col_graphing_h), scrollable=False, background_color="misty rose"),
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
		event, values = w.read()
		print(event, values)

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
	w.close()

if __name__ == "__main__":
	# A way to fake layout updates
	while refresh_window:
		refresh_window = False
		main_loop()