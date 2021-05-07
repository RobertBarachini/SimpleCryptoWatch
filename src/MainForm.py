import PySimpleGUI as sg
import MainFormLayout
import copy

# As PySimpleGUI does not support dynamic layouts out of the box
# we can use a combination of deep copying the layout and then
# recreating the window from scratch ...
refresh_window = True

def main_loop():
	global refresh_window
	refresh_window = False
	window = sg.Window('AutoComplete', copy.deepcopy(MainFormLayout.main_layout), return_keyboard_events=True, finalize=True, font= ('Cascadia Code', 14), resizable=True)
	
	while True:
		event, values = window.read()
		print(event, values)
		if event == sg.WINDOW_CLOSED:
			break
		elif event == "Button":
			MainFormLayout.main_layout.append([sg.Text('This is a very basic PySimpleGUI layout')])
			refresh_window = True
		# Used for "dynamic layouts"
		if refresh_window:
			break
	window.close()

if __name__ == "__main__":
	# A way to fake layout updates
	while refresh_window:
		refresh_window = False
		main_loop()