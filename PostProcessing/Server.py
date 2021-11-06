import Tracking
from flask import Flask, request, flash
import os
import traceback
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
from dash import dash_table
import plotly.subplots as sp
import plotly.graph_objects as go
import plotly.express as px
import pandas
import csv
import os
import json

# TO DO:
#   Proper formatting for dashboard
#   Unit origin of measurements

def StartServer():

    # Get local file path
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Setting variables
    uploadFolder = os.path.join(dir_path, 'Input')

    # Create directory if nonexistent
    if not os.path.exists(uploadFolder):
        os.makedirs(uploadFolder)

    # Create instance folder if nonexistance
    if not os.path.exists(os.path.join(dir_path, 'Instance')):
        os.makedirs(os.path.join(dir_path, 'Instance'))

    # Create secret key if not created
    configPath = os.path.join(dir_path, 'Instance', 'config')
    if not os.path.exists(configPath):
        with open(configPath, 'w') as f:
            secretKey = os.urandom(12).hex()
            f.write(secretKey)
    else:
        with open(configPath, 'r') as f:
            secretKey = f.read()

    # Set up flask server
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = uploadFolder
    app.config['SECRET_KEY'] = secretKey

    # HTTP route handler
    @app.route('/', methods=['POST', 'GET'])
    def uploadFile():
        
        # GET test response
        if request.method == 'GET':
            return 'Successfully pinged server.', 200

        # POST route to accept 
        elif request.method == 'POST':
            
            # Check if POST request has file attached
            if 'file' not in request.files:
                return 'ERROR: No file attached.', 400
            
            # Get file
            file = request.files['file']

            # Check for empty username
            if file.filename == '':
                return 'ERROR: No file attached.', 400

            # Check if test ID is included in form
            if 'test_id' not in request.form:
                return 'ERROR: Test identifier not specified', 400

            # Get test ID
            testID = request.form['test_id']

            # Check for file overwrite
            folderpath = os.path.join(app.config['UPLOAD_FOLDER'], str(testID))
            filepath = os.path.join(folderpath, file.filename)
            if os.path.exists(filepath):
                return 'ERROR: File already exists with that name.', 403

            # Chcek if directory exists for test ID, and create if not
            if not os.path.exists(folderpath):
                os.makedirs(folderpath)

            # Otherwise save to file
            file.save(filepath)

            try:
                Tracking.ProcessFiles(str(testID))
            except Exception as e:
                # Remove failed file
                os.remove(filepath)

                # Save error message
                errorMsg = traceback.format_exc()
                outputMsg =  (
                'ERROR: Upload accepted but could not process file.\n'
                'See Python error traceback below:\n\n')
                return outputMsg + errorMsg, 500

            return 'File successfully processed!', 201

    return app

def GenerateGraphDiv(foldername):

    # Check if no files exist
    if not foldername:
        return html.P(id = 'placeholder', children='File not found on server.')

    # Assemble file paths
    dirPath = os.path.dirname(os.path.realpath(__file__))
    outputPath = os.path.join(dirPath, 'Output', foldername)

    # Get list of files
    fileList = sorted(os.listdir(outputPath))
    fileList = list(filter(lambda name: '.csv' in name, fileList))
    fileList = list(filter(lambda name: name != 'multi.csv', fileList))

    # Collect data from CSV files
    df = [None]*(len(fileList) + 1)
    df[0] = pandas.read_csv(os.path.join(outputPath, 'multi.csv')).round(2)
    for idx, filename in enumerate(fileList):
        df[idx+1] = pandas.read_csv(os.path.join(outputPath, filename)).round(2)

    # Define web page layout
    return [
        html.H1(id = 'H1', children = 'Tracking Results',\
            style = {'textAlign':'center','marginTop':40,'marginBottom':40}),
        html.H2(id = 'H2', children = 'Test Name: \"' + foldername + '\"',\
            style = {'textAlign':'center','marginTop':40,'marginBottom':0})] \
        + [TrackingPlot(df, fr) for fr in range(len(df))]

def TrackingPlot(dataFrame, frameNumber):

    # Set plot config options
    graphConfig = dict({
        'displaylogo'   : False,
        'scrollZoom'    : True
    })

    # Return graph object
    if frameNumber == 0:
        return dcc.Graph(
            id = 'line_plot0', 
            figure = px.line(
                dataFrame[0], 
                title='Multistatic',
                y='Cross-Track Position', 
                x='Along-Track Position', 
                hover_data=['Time']),
            config={**graphConfig, **dict({'toImageButtonOptions':{'filename':'multistatic'}})})
    else:
        return dcc.Graph(
            id = 'scatter_plot' + str(frameNumber), 
            figure = px.scatter(
                dataFrame[frameNumber], 
                title='Unit ' + str(frameNumber),
                y='Cross-Track Position', 
                x='Along-Track Position', 
                hover_data=['Time']),
            config={**graphConfig, **dict({'toImageButtonOptions':{'filename':'unit' + str(frameNumber)}})})

def GenerateDropdown():

    # Assemble file paths
    dirPath = os.path.dirname(os.path.realpath(__file__))
    outputPath = os.path.join(dirPath, 'Output')
    folderList = sorted(os.listdir(outputPath))

    # Generate default value
    if folderList:
        defaultValue = folderList[0]
    else:
        defaultValue = ''

    # Sort by most recent timestamp
    folderList.sort(
        key=lambda name: os.path.getmtime(os.path.join(outputPath, name)),
        reverse=True
    )

    # Generate dropdown
    return html.Div(
        children=[
            dcc.Dropdown(
                id='file-dropdown',
                options=[
                    {'label': folder, 'value': folder}\
                    for folder in folderList
                ],
                value=defaultValue
            )
        ],
        style={'width':'50%', 'textAlign':'center'})

def GenerateParameterTable():

    # Assemble file path
    dirPath = os.path.dirname(os.path.realpath(__file__))
    paramFile = os.path.join(dirPath, 'Instance', 'params.json')

    # If file exists, read from file
    if os.path.exists(paramFile):
        with open(paramFile, 'r') as jsonFile:
            paramsIn = json.load(jsonFile)
    
    # Make parameter list human readable
    paramListReadable = {
        'Maximum Target Speed [m/s]'            : paramsIn['max_vel'],
        'Maximum Target Acceleration [m/s^2]'   : paramsIn['max_acc'],
        'Fine Gating Threshold'                 : paramsIn['dist_thresh'],
        'Cross-Track Motion Variance'           : paramsIn['sigma_v'][0],
        'Along-Track Motion Variance'           : paramsIn['sigma_v'][1]
    }

    # Return HTML object
    return html.Div(
        children = [
            dash_table.DataTable(
                id='param-table',
                columns=([
                    {'id': 'parameter', 'name': 'Parameter'}, 
                    {'id': 'value',     'name': 'Value'}]
                ),
                data=[{'parameter': key, 'value': paramListReadable[key]} \
                    for key in paramListReadable.keys()],
                editable=True
            ),
            html.Button('Re-Process Tracking', 
                id='param-submit',
                n_clicks=0
            )
        ],
        style={'width':'50%'})

def UpdateParameters(newParams):

    try:
        # Generate parameters in file format
        paramsOut = {
            'max_vel'       : float(newParams[0]['value']),
            'max_acc'       : float(newParams[1]['value']),
            'dist_thresh'   : float(newParams[2]['value']),
            'sigma_v'       : [float(newParams[3]['value']), 
                            float(newParams[4]['value'])]
        }

        # Assemble file path
        dirPath = os.path.dirname(os.path.realpath(__file__))
        paramFile = os.path.join(dirPath, 'Instance', 'params.json')

        # Save new parameters to file
        with open(paramFile, 'w') as jsonFile:
            json.dump(paramsOut, jsonFile, indent=4)
    
    except(Exception):
        print("Failed to update parameters.")

def GenerateMainPage():

    # Draw all components
    layout = html.Div(id = 'document', children=[
        html.Div(id = 'param-page', children = GenerateParameterTable()),
        html.Div(id = 'dropdown-page', children = GenerateDropdown()),
        html.Div(id = 'graph-page', children = GenerateGraphDiv(''))
    ])
    return layout

def SetupCallbacks(app):

    # Set up parameter change callback
    @app.callback(
        Output('graph-page', 'children'),
        Input('param-submit', 'n_clicks'),
        Input('param-table', 'data'),
        Input('file-dropdown', 'value')
    )
    def RefreshResults(n_clicks, data, value):
        if n_clicks > RefreshResults.lastClick:
            UpdateParameters(data)
            RefreshResults.lastClick = n_clicks
            if value:
                Tracking.ProcessFiles(value)
        return GenerateGraphDiv(value)
    RefreshResults.lastClick = 0


# Main path
if __name__ == "__main__":
    
    # Start flask server
    flaskServer = StartServer()

    # Initialize Dash app
    app = dash.Dash(
        server=flaskServer,
        url_base_pathname='/dashboard/',
        title='SEMTA Results Viewer'
    )
    
    # Add main page to layout
    app.layout = GenerateMainPage

    # Initialize callback functions
    SetupCallbacks(app)

    # Begin server
    app.run_server(port=5000, host='0.0.0.0', debug=True)