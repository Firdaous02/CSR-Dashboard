# Import necessary libraries
import dash
from dash import Dash, dcc, html, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State, MATCH
import pandas as pd
import base64
import io
import datetime
from sqlalchemy import create_engine
from sqlalchemy import text

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)

app.config.suppress_callback_exceptions = True

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
                                    id="edit-button",  # Add id for the edit button
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
                                    id="export-button",
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

# Modal for editing data
edit_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Edit Data")),
        dbc.ModalBody(
            dash_table.DataTable(
                id='edit-table',
                columns=[{"name": i, "id": i} for i in ['unique_id', 'OFFICE', 'FISCAL_YEAR', 'MONTH', 'SURVEY_GROUP', 'SOLD_TO', 'GLOBAL_CUSTOMER', 'SOLD_TO_NAME', 'FIRST_NAME', 'LAST_NAME', 'EMAIL', 'OVERALL_SATISFACTION', 'CUSTOMER_SERVICE_REPRESENTATIVE_SATISFACTION', 'EASE_OF_DOING_BUSINESS', 'ADDITIONNAL_COMMENTS', 'CUSTOMER_SATISFACTION_INDEX']],
                editable=True,
                row_deletable=True,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'color': 'black'},
            ),
            style={"maxHeight": "60vh", "overflowY": "auto"}
        ),
        dbc.ModalFooter(
            dbc.Button("Save Changes", id="save-changes", className="ml-auto")
        ),
    ],
    id="edit-modal",
    size="lg",
)

export_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Export Data Options")),
        dbc.ModalBody(
            [
                dbc.RadioItems(
                    id='export-option',
                    options=[
                        {'label': 'Export All Data', 'value': 'all'},
                        {'label': 'Export by Fiscal Year', 'value': 'fiscal_year'},
                        {'label': 'Export by Month', 'value': 'month'}
                    ],
                    value='all',
                ),
                # Static inputs for fiscal year and month, hidden by default
                    dbc.Input(
                        id='fiscal-year-input',
                        placeholder="Enter Fiscal Year",
                        type="text",
                        style={'margin-top': '10px', 'display': 'none'}  # Hidden by default
                    ),
                    dcc.Dropdown(
                        id='month-dropdown',
                        options=[
                            {'label': 'January', 'value': 'JANUARY'},
                            {'label': 'February', 'value': 'FEBRUARY'},
                            {'label': 'March', 'value': 'MARCH'},
                            {'label': 'April', 'value': 'APRIL'},
                            {'label': 'May', 'value': 'MAY'},
                            {'label': 'June', 'value': 'JUNE'},
                            {'label': 'July', 'value': 'JULY'},
                            {'label': 'August', 'value': 'AUGUST'},
                            {'label': 'September', 'value': 'SEPTEMBER'},
                            {'label': 'October', 'value': 'OCTOBER'},
                            {'label': 'November', 'value': 'NOVEMBER'},
                            {'label': 'December', 'value': 'DECEMBER'}
                        ],
                        placeholder="Select Month",
                        style={'margin-top': '10px', 'display': 'none'},  # Hidden by default
                        className='dropdown-option'
                    )
                ]
            ),
        dbc.ModalFooter(
            dbc.Button("Export", id="confirm-export", className="ml-auto")
        ),
    ],
    id="export-modal",
    size="lg",
    is_open=False
)

# Define the layout of the app
app.layout = html.Div(
    style={'backgroundColor': '#1e2c3c', 'padding': '20px'},  # Set the background color and text color
    children=[
        navbar,  # Add the navbar with the logo
        sidebar,  # Add the sidebar
        html.Div(id='output-data-upload'),
        edit_modal,  # Add the edit modal
        dcc.Download(id="download-dataframe-xlsx"),
        export_modal,  # Add the export modal
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

# Combined callback to open the modal, load data, and save changes
@app.callback(
    Output("edit-modal", "is_open"),
    Output("edit-table", "data"),
    Input("edit-button", "n_clicks"),
    Input("save-changes", "n_clicks"),
    State("edit-modal", "is_open"),
    State("edit-table", "data")
)
def toggle_modal_edit(edit_n_clicks, save_n_clicks, is_open, table_data):
    ctx = callback_context

    if not ctx.triggered:
        return is_open, dash.no_update

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "edit-button":
        if edit_n_clicks:
            # Load data from database
            query = "SELECT * FROM data"
            df = pd.read_sql(query, con=engine)
            return not is_open, df.to_dict('records')
        return is_open, dash.no_update
    
    elif button_id == "save-changes":
        if save_n_clicks:
            df = pd.DataFrame(table_data)

            df.to_sql('DATA', con=engine, if_exists='replace', index=False)
            return not is_open, dash.no_update
    
    return is_open, dash.no_update

# Toggle Export Modal
@app.callback(
    Output("export-modal", "is_open"),
    Input("export-button", "n_clicks"),
    State("export-modal", "is_open")
)
def toggle_export_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# Show/Hide Inputs Based on Export Option
@app.callback(
    [Output('fiscal-year-input', 'style'),
     Output('month-dropdown', 'style')],
    Input('export-option', 'value')
)
def toggle_export_inputs(option):
    if option == 'fiscal_year':
        return {'display': 'block'}, {'display': 'none'}  # Show fiscal year input, hide month dropdown
    elif option == 'month':
        return {'display': 'block'}, {'display': 'block'}  # Hide fiscal year input, show month dropdown
    return {'display': 'none'}, {'display': 'none'}  # Hide both by default

# Export Data
@app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input('confirm-export', 'n_clicks'),
    State('export-option', 'value'),
    State('fiscal-year-input', 'value'),
    State('month-dropdown', 'value'),
    prevent_initial_call=True
)
def export_data(n_clicks, export_option, fiscal_year, month):
    if n_clicks is None:
        return dash.no_update

    if export_option == 'fiscal_year' and fiscal_year:
        if not fiscal_year.isdigit():
            return html.Div(['Please enter a valid fiscal year.'])
        query = f"SELECT * FROM DATA WHERE FISCAL_YEAR = '{fiscal_year}'"
        filename = f"CSI_Data_{fiscal_year}.xlsx"

    elif export_option == 'month' and month and fiscal_year:
        query = f"SELECT * FROM DATA WHERE MONTH = '{month}' AND FISCAL_YEAR = '{fiscal_year}'"
        filename = f"CSI_Data_{month}_{fiscal_year}.xlsx"
    else:
        query = "SELECT * FROM DATA"
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        filename = f"CSI_All_Data_{today}.xlsx"

    # Retrieve and export data from the database
    try:
        df = pd.read_sql(query, con=engine)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        return dcc.send_bytes(output.getvalue(), filename)
    
    except Exception as e:
        return html.Div([
            f'An error occurred while exporting data: {str(e)}'
        ])


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
