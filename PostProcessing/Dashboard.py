import dash
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import plotly.express as px
import csv

with open('Output/AsyncTracking/multi.csv', newline='') as csvfile:
    multiReader = csv.reader(csvfile)
    multiData = list(multiReader)

xData = [x[3] for x in multiData]
yData = [x[2] for x in multiData]

app = dash.Dash()

def multiPlot():
    fig = go.Figure([go.Scatter(x = xData, y = yData)])
    fig.update_layout(title = 'Multistatic Tracking Data')
    return fig

app.layout = html.Div(id = 'parent', children = [
    html.H1(id = 'H1', children = 'Styling using html components',\
        style = {'textAlign':'center','marginTop':40,'marginBottom':40}),
        dcc.Graph(id = 'line_plot', figure = multiPlot())    
    ])

if __name__ == '__main__': 
    app.run_server()