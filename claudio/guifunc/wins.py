from pino.config import Config
import PySimpleGUI as sg
import glob
import os
from datetime import datetime

def set_config(yaml_path: str) -> dict:
    global x, y
    ymlPath = glob.glob(yaml_path)
    ymlFile = [os.path.basename(i) for i in ymlPath]

    BtoP = Config("./config/gui/box2port.yml")
    BPKey = [key for key in BtoP.get_metadata().keys()]
    radioButton = []
    for i in range(0, len(BPKey)):
        radioButton.append(sg.Radio(f'{BPKey[i]}', 'Radio1', key = f'{BPKey[i]}'))

    sg.SetOptions(text_justification='left', font = ('Hack', 13))
    layout =[[sg.Text('Set Your Experiment', justification = 'center', font = ('Hack', 15), size = (50,1))],
            [sg.Text('config file: ', size = (13, 1)), sg.Combo(values = ymlFile, readonly = True, auto_size_text = True, key = 'path')],
            [sg.Text('chamber: ', size = (13,1)), sg.Frame(layout = [radioButton],
                  title='',title_color='black', element_justification = 'center', border_width = 5)],
            [sg.Text('')],
            [sg.Cancel(), sg.Button('Submit', pad = (20,(5,0)))]]

    win_set_yml = sg.Window('set yaml file', layout)

    while True:
        event, values = win_set_yml.read()
        x, y = win_set_yml.CurrentLocation()
        if event in (None, 'Cancel'):
            sys.exit()
            break
        if event == 'Submit':
            if values['path'] != "":
                config = Config("./config/gui/" + f'{values["path"]}')
                for i in range(0, len(BPKey)):
                    if values[f'{BPKey[i]}'] == True:
                        chamber = BPKey[i]
                        port = BtoP.get_metadata()[f'{BPKey[i]}']
                        config['Comport']['port'] = port
                        config['chamber'] = chamber
                try:
                    port
                    break
                except NameError:
                    sg.popup('No Chamber selected!', location = (x, y))
            else:
                sg.popup('No File selected!', location = (x, y))

    win_set_yml.close()
    return config


def set_filename(config: dict) -> str:
    global x, y
    cols = []
    chamber = config['chamber']
    for els in list(config['Experimental'].items()):
        cols.append([sg.Text(f'{els[0]}:', justification = 'right', size = (15,1)),
            sg.Text(f'{els[1]}', size =(20,1), background_color = 'blue')])

    layout = [[sg.Text('Experimental Parameters', font = ('Hack', 15))],
            [sg.Frame('parameters', [[sg.Column(cols, background_color = 'white')],[sg.Text('', size = (30,1)), sg.Button('revise')]])],
            [sg.Text('')],
            [sg.Text("Experimenter: "), sg.Input('', size = (30, 1), key = 'experimenter')],
            [sg.Text("data file: "), sg.Input('', size = (25, 1), key = 'dataFile'), sg.Text('.csv', justification = 'left')],
            [sg.Cancel(), sg.Button('submit')]]

    window = sg.Window(f'{chamber}', layout, location = (x, y))
    window2_active = False

    while True:                  # the event loop
        event, values = window.read()
        x, y = window.CurrentLocation()
        if event in (None, 'Cancel'):
            sys.exit()
            break
        if event == "submit":
            if values['dataFile'] != "" and values['experimenter'] != "":
                break
            else:
                sg.popup('Specify Experimenter and FileName!', location = (x, y))
                event, values = window.read()
        if event == 'revise' and not window2_active:
            window2_active = True
            layout2 = []
            for els in list(config['Experimental'].items()):
                layout2.append([sg.Text(f'{els[0]} :', justification = 'right', size = (15,1)),
                    sg.Input(f'{els[1]}', key = f'{els[0]}')])

            layout2.append([sg.Cancel(), sg.Button('save')])
            window2 = sg.Window('settings', layout2)
            while True:
                ev2, val2 = window2.read()
                if ev2 in (None, 'Cancel'):
                    window2.Close()
                    window2_active = False
                    break
                if ev2 == 'save':
                    sg.popup('Not implemented! :)')

    filename = values["dataFile"] + "_" + \
            config['Experimental']['schedule'] + "_" + \
            f"{chamber}" + "_" + \
            values["experimenter"] + "_" + \
            datetime.now().strftime("%m-%d-%H-%M") + ".csv"
    window.close()
    return filename

