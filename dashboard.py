from dash import html
import dash
from dash import Dash, dcc, html, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State, MATCH
import pandas as pd
import plotly.express as px
import base64
import io
import datetime
from sqlalchemy import create_engine
from sqlalchemy import text

from flask import session

# Define the figures for the graphs

# # 1. Response Rate - Line Graph
# line_fig = go.Figure(
#     data=[
#         go.Scatter(
#             x=['Cust 1', 'Cust 2', 'Cust 3', 'Cust 4', 'Cust 5'],
#             y=[10, 15, 8, 12, 9],
#             mode='lines+markers',
#             line=dict(color='cyan', width=2)
#         )
#     ]
# )
# line_fig.update_layout(
#     title='Response Rate',
#     paper_bgcolor='rgba(0, 0, 0, 0)',
#     plot_bgcolor='rgba(0, 0, 0, 0)',
#     font_color='white',
# )

# # 2. CSI Average - Bar Graph
# bar_fig = go.Figure(
#     data=[
#         go.Bar(
#             x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'],
#             y=[5, 10, 15, 7, 12, 17, 20, 22, 25],
#             marker=dict(color='orange')
#         )
#     ]
# )
# bar_fig.update_layout(
#     title='CSI Average',
#     paper_bgcolor='rgba(0, 0, 0, 0)',
#     plot_bgcolor='rgba(0, 0, 0, 0)',
#     font_color='white',
# )

# # 3. Percentage of Every Level of CSI - Pie Chart
# pie_fig = go.Figure(
#     data=[
#         go.Pie(
#             labels=['Very Satisfied', 'Satisfied', 'Neutral', 'Unsatisfied', 'Very Unsatisfied'],
#             values=[40, 30, 15, 10, 5],
#             hole=.3
#         )
#     ]
# )
# pie_fig.update_layout(
#     title='Percentage of Every Level of CSI',
#     paper_bgcolor='rgba(0, 0, 0, 0)',
#     font_color='white'
# )

# # 4. Custom Graph - Treemap
# treemap_fig = go.Figure(
#     go.Treemap(
#         labels=['Cust 1', 'Cust 2', 'Cust 3', 'Cust 4', 'Cust 5', 'Cust 6', 'Cust 7'],
#         parents=['', '', '', '', '', '', ''],
#         values=[10, 20, 30, 40, 50, 60, 70],
#         marker=dict(colors=['#4c78a8', '#9ecae9', '#f58518', '#ffbf79', '#54a24b', '#88d27a', '#b79a20'])
#     )
# )
# treemap_fig.update_layout(
#     title='Custom Graph',
#     paper_bgcolor='rgba(0, 0, 0, 0)',
#     font_color='white'
# )

# Sidebar definition

def dashboard_layout():
    # role = session.get('role', None)
    sidebar = dbc.Offcanvas(
    html.Div(
        [
            html.H2("Dashboard", className="display-4"),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink("Customer Satisfaction Index (CSI)", href="#", active="exact"),
                    dbc.NavLink("KPI2", href="#", active="exact"),
                    dbc.NavLink("KPI3", href="#", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
            html.Div(style={"flex-grow": 1}),  # Pour forcer le bouton de déconnexion à être en bas
            dbc.Row(
                dbc.Col(
                    html.Div(id='user-management-div'),
                    width={"size": 6, "offset": 3},
                )
            ),
            dcc.Location(id='url', refresh=False),

            # html.Div(
            #     [
            #         html.A("User Management", href="/user-management", style={"display": "block"})
            #     ],
            #     style={"display": "block"} if role == 'admin' else {"display": "none"}
            # ),        
            dbc.Button("Logout", id="logout-link", className="mt-5", style={"color": "white"}),  # Lien de déconnexion
        ],
        style={"height": "100%", "display": "flex", "flex-direction": "column"},  # Ajustement pour aligner en bas
    ),
    id="sidebar",
    title="Menu",
    is_open=False,
    style={"background-color": "#1e2c3c"},
    )
    logout_modal = dbc.Modal(
        [
            dbc.ModalHeader("Confirm Logout"),
            dbc.ModalBody("Do you really want to logout?"),
            dbc.ModalFooter(
                [
                    dbc.Button("Yes", id="confirm-logout", color="danger"),  # Bouton pour confirmer la déconnexion
                    dbc.Button("No", id="cancel-logout", color="secondary"),  # Bouton pour annuler la déconnexion
                ]
            ),
        ],
        id="logout-modal",
        is_open=False,
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
                                dbc.Col(dbc.NavbarBrand("CSR Dashboard", className="ml-2"), width="auto"),
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
                                            style={"color": "black"},  # Set text color to black
                                            n_clicks=0
                                        ),
                                        style={'display': 'none'}
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
                                        style={"color": "black", 'display': 'none'}, # Set text color to black
                                        n_clicks=0
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
                            multi=True,
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
    from datetime import datetime
    current_year = datetime.now().year



    dashboard_layout = html.Div(
        style={'backgroundColor': '#1e2c3c', 'padding': '20px'},  # Set the background color and text color
        children=[
            navbar,  # Add the navbar with the logo
            sidebar,  # Add the sidebar
            logout_modal,
            # dcc.Location(id='url'),
            dcc.Store(id='nclicks-store'),
            html.Div(id='output-data-upload'),
            html.Div(id='output-message', className='alert-message'),
            edit_modal,  # Add the edit modal
            dcc.Download(id="download-dataframe-xlsx"),
            export_modal,  # Add the export modal
            html.Div(
                style={'padding': '20px'},  # Adjust the padding
                children=[
                    dbc.Row([
                        dbc.Col(
                        dcc.Dropdown(
                            id='filter-dropdown',
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
                                id='fiscal-year-input-filter',
                                placeholder=str(current_year),
                                value=current_year,
                                style={'color': '#000', 'display': 'block'},
                                type='number'
                            ),
                            width=2,
                            className="d-flex align-items-center justify-content-center"
                        ),

                    ]),
                    
                    dbc.Row([
                        dbc.Col([html.Button("Exporter Line Graph", id="export-line", n_clicks=0),
                                    dcc.Graph(id='line-graph')], width=6),
                        dbc.Col([html.Button("Exporter Bar Graph", id="export-bar", n_clicks=0), dcc.Graph(id='bar-graph')], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([html.Button("Exporter Pie Graph", id="export-pie", n_clicks=0), dcc.Graph(id='pie-graph')], width=6),
                        dbc.Col([html.Button("Exporter Treemap Graph", id="export-treemap", n_clicks=0), dcc.Graph(id='treemap-graph')], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([html.Button("Exporter Evolution Bar Graph", id="export-evolution-bar", n_clicks=0), dcc.Graph(id='bar-evolution-graph')], width=12),
                    ]),
                    dbc.Row([
                        dbc.Col(
                            [html.Button("Exporter Comments", id="export-comments", n_clicks=0),
                            dash_table.DataTable(
                                id='comments-table',
                                style_table={'height': 'auto', 'overflowY': 'auto'},
                                style_header={'backgroundColor': '#1e2c3c', 'color': 'white', 'textAlign' :'center'},
                                style_data={'backgroundColor': '#2c3e50', 'color': 'white', 'overflow': 'hidden',  # Évite le défilement horizontal
                                            'textOverflow': 'ellipsis',},
                                style_cell={
                                    'textAlign': 'left',  # Alignement du texte à gauche
                                    'whiteSpace': 'normal',  # Texte sur plusieurs lignes
                                    'height': 'auto',  # Hauteur automatique des cellules
                                },
                                columns=[
                                    {'name': 'Office', 'id': 'OFFICE'},
                                    {'name': 'Fiscal Year', 'id': 'FISCAL_YEAR'},
                                    {'name': 'Month', 'id': 'MONTH'},
                                    {'name': 'Global Customer', 'id': 'GLOBAL_CUSTOMER'},
                                    {'name': 'Customer Name', 'id': 'name'},
                                    {'name': 'Comments', 'id': 'ADDITIONNAL_COMMENTS'},
                                ],
                                page_size=7,  # Number of rows per page
                            )],
                            width=12
                        )
                    ]),
                dcc.Download(id="download-graphs-dataframe-xlsx"),

                ]
            ),
        ]
    )
    return dashboard_layout