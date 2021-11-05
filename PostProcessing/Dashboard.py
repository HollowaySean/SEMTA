import dash
from dash import html
from dash import dcc
import plotly.graph_objects as go
import plotly.express as px
import pandas
import csv

# with open('Output/AsyncTracking/multi.csv', newline='') as csvfile:
#     multiReader = csv.reader(csvfile)
#     multiData = list(multiReader)

# xData = [x[3] for x in multiData]
# yData = [x[2] for x in multiData]
df = pandas.read_csv('Output/AsyncTracking/multi.csv')

fig = px.scatter(df, y='Cross-Range Position', x='Down-Range Position', hover_data=['Frame Time'])
fig.show()

# app = dash.Dash()

# def multiPlot():
#     fig = go.Figure([px.scatter(df, x='Cross-Range Position', y='Down-Range Position')])
#     fig.update_layout(title = 'Multistatic Tracking Data')
#     return fig

# app.layout = html.Div(id = 'parent', children = [
#     html.H1(id = 'H1', children = 'Multistatic Tracking Results',\
#         style = {'textAlign':'center','marginTop':40,'marginBottom':40}),
#     dcc.Graph(id = 'line_plot', figure = multiPlot())    
#     ])

# if __name__ == '__main__': 
#     app.run_server()