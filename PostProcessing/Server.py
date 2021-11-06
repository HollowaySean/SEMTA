import Tracking
from flask import Flask, request, flash
import os
import traceback
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
import plotly.subplots as sp
import plotly.graph_objects as go
import plotly.express as px
import pandas
import csv
import os

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
    return html.Div(id = 'parent', children = [
        html.H1(id = 'H1', children = 'Tracking Results',\
            style = {'textAlign':'center','marginTop':40,'marginBottom':40}),
        html.H2(id = 'H2', children = 'Test Name: \"' + foldername + '\"',\
            style = {'textAlign':'center','marginTop':40,'marginBottom':0})] +

        [TrackingPlot(df, fr) for fr in range(len(df))]
        )

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
                value=folderList[0]
            )
        ],
        style={'width':'50%', 'textAlign':'center'})

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

    # Draw graphs
    graphDiv = GenerateGraphDiv('AsyncTracking')
    dropdownDiv = GenerateDropdown()
    app.layout = html.Div([
        dropdownDiv,
        html.Div(id = 'graph-page', children = [
            graphDiv
        ])
    ])

    @app.callback(
        Output('graph-page', 'children'),
        Input('file-dropdown', 'value')
    )
    def UpdatePlots(value):
        return GenerateGraphDiv(value)
    
    # Begin server
    app.run_server(port=5000, host='0.0.0.0', debug=True)