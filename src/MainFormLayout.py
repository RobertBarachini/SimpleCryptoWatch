# Functions for constructing the layout for PySimpleGui

import PySimpleGUI as sg

main_layout = [
	[
		[sg.Text('Thi is a very basic PySimpleGUI layout')],
		[sg.Input()],
		[sg.Button('Button'), sg.Button('Exit')]
	],
	[
		[sg.Text('Thi is a very basic PySimpleGUI layout')],
		[sg.Input()],
		[sg.Button('Button'), sg.Button('Exit')]
	]
]

#load images into elements
image_elem1 = sg.Text('Image   1   attribute    item    ')
image_elem2 = sg.Text('Image   1   attribute    item    ')

#img 1 attributes list
col_21 =[
        [sg.Text('Image   1   attribute    item    '), sg.Button(button_text="Update") ],
        [sg.Text('Image   1   attribute    item    '), sg.Button(button_text="Update") ],
        [sg.Text('Image   1   attribute    item    '), sg.Button(button_text="Update") ]]

#img 2 attributes list
col_22 =[
        [sg.Text('Image   2   attribute    item    '), sg.Button(button_text="Update") ],
        [sg.Text('Image   2   attribute    item    '), sg.Button(button_text="Update") ],
        [sg.Text('Image   2   attribute    item    '), sg.Button(button_text="Update") ]]

main_layout = [[image_elem1, sg.Frame(layout=col_21, title='')],
          [image_elem2, sg.Frame(layout=col_22, title='')]]

# main_layout = [[
# 	sg.Frame('Input data',[[
# 		sg.Text('Input:'),      
# 		sg.Input(do_not_clear=False),      
# 		sg.Button('Read'), sg.Exit(),
# 		sg.Text('Alternatives:'),
# 		sg.Listbox(values=('alternatives...', ''), size=(30, 2), key='_LISTBOX_')
# 	]])
# ]]

# main_layout = [
#                 [sg.Column([
#                     sg.Text('PvP Module'),
#                     sg.Checkbox(
#                         'Enabled',
#                         key='pvp.enabled',
#                         enable_events=True)
#                 ])],
#                 [sg.Column([
#                     sg.Text('Fleet Preset'),
#                     sg.Checkbox(
#                         'Enabled',
#                         key='pvp.neki',
#                         enable_events=True)
#                 ])]
#             ]