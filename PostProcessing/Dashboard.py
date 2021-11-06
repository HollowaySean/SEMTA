import dash
from dash import html
from dash import dcc
import plotly.subplots as sp
import plotly.graph_objects as go
import plotly.express as px
import pandas
import csv
import os

def startServer(foldername):

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

    # Initialize Dash app
    app = dash.Dash()

    # Define web page layout
    app.layout = html.Div(id = 'parent', children = [
        html.H1(id = 'H1', children = 'Tracking Results',\
            style = {'textAlign':'center','marginTop':40,'marginBottom':40}),
        html.H2(id = 'H2', children = 'Test Name: \"' + foldername + '\"',\
            style = {'textAlign':'center','marginTop':40,'marginBottom':0})] +

        [dcc.Graph(
            id = 'line_plot0', 
            figure = px.line(
                df[0], 
                title='Multistatic',
                y='Cross-Track Position', 
                x='Along-Track Position', 
                hover_data=['Time']))] +

        [dcc.Graph(
            id = 'scatter_plot' + str(fr), 
            figure = px.scatter(
                df[fr], 
                title='Unit ' + str(fr),
                y='Cross-Track Position', 
                x='Along-Track Position', 
                hover_data=['Time']))\
        for fr in range(1,len(df))]
        )

    # Begin server
    app.run_server(debug=True)

if __name__ == '__main__': 
    startServer('AsyncTracking')