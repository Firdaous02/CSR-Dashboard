# Import necessary libraries
import dash
from dash import Dash, dcc, html, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import pandas as pd
import base64
import io
from sqlalchemy import create_engine
from sqlalchemy import text

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

engine = create_engine('mssql+pyodbc://@localhost/CSIData?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes')

# Define the figures for the graphs

# 1. Response Rate - Line Graph
line_fig = go.Figure(
    data=[
        go.Scatter(
            x=['Cust 1', 'Cust 2', 'Cust 3', 'Cust 4', 'Cust 5'],
            y=[10, 15, 8, 12, 9],
            mode='lines+markers',
            line=dict(color='cyan', width=2)
        )
    ]
)
line_fig.update_layout(
    title='Response Rate',
    paper_bgcolor='rgba(0, 0, 0, 0)',
    plot_bgcolor='rgba(0, 0, 0, 0)',
    font_color='white',
)

# 2. CSI Average - Bar Graph
bar_fig = go.Figure(
    data=[
        go.Bar(
            x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'],
            y=[5, 10, 15, 7, 12, 17, 20, 22, 25],
            marker=dict(color='orange')
        )
    ]
)
bar_fig.update_layout(
    title='CSI Average',
    paper_bgcolor='rgba(0, 0, 0, 0)',
    plot_bgcolor='rgba(0, 0, 0, 0)',
    font_color='white',
)

# 3. Percentage of Every Level of CSI - Pie Chart
pie_fig = go.Figure(
    data=[
        go.Pie(
            labels=['Very Satisfied', 'Satisfied', 'Neutral', 'Unsatisfied', 'Very Unsatisfied'],
            values=[40, 30, 15, 10, 5],
            hole=.3
        )
    ]
)
pie_fig.update_layout(
    title='Percentage of Every Level of CSI',
    paper_bgcolor='rgba(0, 0, 0, 0)',
    font_color='white'
)

# 4. Custom Graph - Treemap
treemap_fig = go.Figure(
    go.Treemap(
        labels=['Cust 1', 'Cust 2', 'Cust 3', 'Cust 4', 'Cust 5', 'Cust 6', 'Cust 7'],
        parents=['', '', '', '', '', '', ''],
        values=[10, 20, 30, 40, 50, 60, 70],
        marker=dict(colors=['#4c78a8', '#9ecae9', '#f58518', '#ffbf79', '#54a24b', '#88d27a', '#b79a20'])
    )
)
treemap_fig.update_layout(
    title='Custom Graph',
    paper_bgcolor='rgba(0, 0, 0, 0)',
    font_color='white'
)

# Sidebar definition
sidebar = dbc.Offcanvas(
    html.Div(
        [
            html.H2("Dashboard", className="display-4"),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink("Home", href="#", active="exact"),
                    dbc.NavLink("Analytics", href="#", active="exact"),
                    dbc.NavLink("Settings", href="#", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
    ),
    id="sidebar",
    title="Menu",
    is_open=False,
    style={"background-color": "#1e2c3c"},
)

# Navbar with logo
navbar = dbc.Navbar(
    dbc.Container(
        dbc.Row(
            [
                # Left side with toggle, logo, and title
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Col(dbc.Button("☰", id="open-sidebar", n_clicks=0, color="primary"), width="auto"),
                            dbc.Col(html.Img(src="/assets/logo.png", height="40px"), width="auto"),
                            dbc.Col(dbc.NavbarBrand("CSI Dashboard", className="ml-2"), width="auto"),
                        ],
                        align="center",
                        className="g-0"
                    ),
                    width="auto"
                ),
                
                # Spacer in the middle
                dbc.Col(width=True),  # This column will expand to take the remaining space
                
                # Right side with buttons
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Upload(
                                    id='upload-data',
                                    children=dbc.Button(
                                        [
                                            html.Img(src="/assets/import-icon.png", height="20px", style={"margin-right": "5px"}),
                                            "Import Data"
                                        ],
                                        color="warning",
                                        className="mr-2",
                                        style={"color": "black"}  # Set text color to black
                                    ),
                                    style={'display': 'inline-block'}
                                ),
                                width="auto"
                            ),
                            dbc.Col(
                                dbc.Button(
                                    [
                                        html.Img(src="/assets/edit-icon.png", height="20px", style={"margin-right": "5px"}),
                                        "Edit"
                                    ],
                                    color="light",
                                    className="mr-2",
                                    style={"color": "black"}  # Set text color to black
                                ),
                                width="auto"
                            ),
                            dbc.Col(
                                dbc.Button(
                                    [
                                        html.Img(src="/assets/export-icon.png", height="20px", style={"margin-right": "5px"}),
                                        "Export"
                                    ],
                                    color="primary",
                                    style={"color": "black"}  # Set text color to black
                                ),
                                width="auto"
                            ),
                        ],
                        align="center",
                        className="g-0",
                        justify="end"
                    ),
                    width="auto"
                ),
            ],
            align="center",
            className="g-0 flex-nowrap w-100"
        ),
        fluid=True,
    ),
    color="dark",
    dark=True,
    className="mb-3",
)


# Define the layout of the app
app.layout = html.Div(
    style={'backgroundColor': '#1e2c3c', 'padding': '20px'},  # Set the background color and text color
    children=[
        navbar,  # Add the navbar with the logo
        sidebar,  # Add the sidebar
        html.Div(id='output-data-upload'),
        html.Div(
            style={'padding': '20px'},  # Adjust the padding
            children=[
                dbc.Row([
                    dbc.Col(
                    dcc.Dropdown(
                        options=[
                            {'label': 'By Global Customer', 'value': 'global'},
                            {'label': 'By Ship to', 'value': 'ship_to'},
                            {'label': 'By Office', 'value': 'office'}
                        ],
                        value='global',
                        clearable=False,
                        style={'color': '#000'}
                    ),
                width=4,
                className="align-items-center"
            ),
            dbc.Col(
                dcc.Input(
                    placeholder="2024",
                    style={'color': '#000'}
                ),
                width=2,
                className="d-flex align-items-center justify-content-center"
            ),
                ]),
                
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=line_fig), width=6),
                    dbc.Col(dcc.Graph(figure=bar_fig), width=6),
                ]),
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=pie_fig), width=6),
                    dbc.Col(dcc.Graph(figure=treemap_fig), width=6),
                ])
            ]
        ),
    ]
)

# Callback to toggle the sidebar
@app.callback(
    Output("sidebar", "is_open"),
    Input("open-sidebar", "n_clicks"),
    State("sidebar", "is_open"),
)
def toggle_sidebar(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        connection = engine.connect()
        connection.close()  # Close the connection
    except Exception as e:
        return html.Div(
            f'Database connection error : {str(e)}',
            className='alert alert-danger'
        )

    try:
        if 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return html.Div(
                'File format not supported.',
                className='alert alert-danger'
            )
    except Exception as e:
        return html.Div(
            f'There was an error processing this file: {str(e)}',
            className='alert alert-danger'
        )
    
    try:
        # Créez la colonne "unique_id" en combinant les valeurs de six colonnes
        df['unique_id'] = (
            df['OFFICE'].astype(str) + '_' +
            df['FISCAL_YEAR'].astype(str) + '_' +
            df['MONTH'].astype(str) + '_' +
            df['SOLD_TO'].astype(str) + '_' +
            df['FIRST_NAME'].astype(str) + '_' +
            df['LAST_NAME'].astype(str)
        )

        # Récupérer les unique_id existants dans la base de données
        existing_ids = pd.read_sql("SELECT unique_id FROM data", con=engine)
        existing_ids_set = set(existing_ids['unique_id'])
        
        # Filtrer le DataFrame pour ne conserver que les nouveaux enregistrements
        df_to_insert = df[~df['unique_id'].isin(existing_ids_set)]
        
        if not df_to_insert.empty:
            # Insérer les nouveaux enregistrements
            df_to_insert.to_sql('data', con=engine, if_exists='append', index=False)
        else:
            return html.Div(
                'No new data to insert. All records already exist in the database.',
                className='alert alert-info'
            )

    except Exception as e:
        return html.Div(
            f'An error occurred while inserting data into the database: {str(e)}',
            className='alert alert-danger'
        )

    return html.Div(
        'Data successfully inserted into the database.',
        className='alert alert-success'
    )




@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])

def update_output(contents, filename):
    if contents is not None:
        children = parse_contents(contents, filename)
        return children


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
