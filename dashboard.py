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
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from db import count_onhold_issues


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
    onhold_count = count_onhold_issues()
    # role = session.get('role', None)
    
    sidebar = dbc.Offcanvas(
    html.Div(
        [
            
            # KPI Links
            dbc.Nav(
                [
                    dbc.NavLink("Customer Satisfaction Index (CSI)", href="#", active="exact", style={"border": "none", "color": "white"}),
                    dbc.NavLink("KPI2", href="#", active="exact", style={"border": "none", "color": "white"}),
                    dbc.NavLink("KPI3", href="#", active="exact", style={"border": "none", "color": "white"}),
                ],
                vertical=True,
                pills=True,
                className="mb-3"
            ),

            # Spacer
            html.Div(style={"flex-grow": 1}),
            
            dbc.Row([], style={"height": "300px"}),
            # Divider line and buttons at the bottom
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(id="user-management-div"),  # Hidden by default
                        # dbc.Button("User Management", id="user-management-link", className="mr-2", style={"background-color": "#00b4ef", "border-color": "#00b4ef", "color": "black" }),
                        width={"size": 12},
                        className="mb-2 text-center"
                    ),

                ],
            
                style={"margin-top": "auto"},
                
            ),
            # User Guide Button spanning both columns
            dbc.Row(
                dbc.Col(
                    html.Div(id="user-guide-div"), #Hidden
                    #dbc.Button("User Guide", id="user-guide-link", style={"background-color": "#00b4ef", "border-color": "#00b4ef", "color": "black", "width": "100%"}),
                    width={"size": 12},
                    className="mb-2 text-center"
                )
            ),

            dbc.Row(
                [
                dbc.Col(
                        dbc.Button("Logout", id="logout-link", style={"background-color": "#ff7700", "border-color": "#ff7700", "color": "black", "width": "100%"}),
                        width={"size": 12},
                        className="mb-2 text-center"
                    ),

                ], 
                style={"margin-top": "auto"},
                
            ),   
            
            # Location component for URL routing
            dcc.Location(id='url', refresh=False),
        ],
        style={"height": "100%", "display": "flex", "flex-direction": "column"},  # Ajustement pour aligner en bas
    ),
    title="Dashboard Menu",
    id="sidebar",
    is_open=False,
    style={"background-color": "#1B2131"},

    )
    logout_modal = dbc.Modal(
        [
            dbc.ModalHeader("Confirm Logout",style={"background-color": "#1B2131","family":"Trebuchet MS", "color": "white","border-bottom": "none"}),
            dbc.ModalBody("Are you sure you want to logout?", style={ "background-color": "#1B2131", "color": "white","border-bottom": "none" }),
            dbc.ModalFooter(
                [
                    dbc.Button("Yes", id="confirm-logout", style={"background-color": "#ff7700", "border-color": "#ff7700","color": "black",  }),  # Bouton pour confirmer la déconnexion
                    dbc.Button("No", id="cancel-logout", style={"background-color": "#00b4ef","border-color": "#00b4ef","color": "black" }), # Bouton pour annuler la déconnexion

                ],
            style={"background-color": "#1B2131","border-top": "none"}
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
                            dbc.Col(dbc.Button("☰", id="open-sidebar", n_clicks=0, color="white"), width="auto"),
                            dbc.Col(html.Img(src="/assets/logo.png", height="60px"), width="auto"),
                            dbc.Col(dbc.NavbarBrand("Customer Service Dashboard", className="ml-2",style={"color":"white","font-size":"24px", "margin-left": "10px"}), width="auto"),
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
                                        style={"color": "black", "margin-right": "5px"},  # Increased margin between buttons
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
                                    id="edit-button",
                                    color="light",
                                    style={"color": "black", 'display': 'none', "margin-right": "20px"}, # Increased margin between buttons
                                    n_clicks=0
                                ),
                                width="auto"
                            ),
                            dbc.Col(
                                dbc.Button(
                                    [
                                        html.Img(src="/assets/image.png", height="20px", style={"margin-right": "5px"}),
                                        "Export"
                                    ],
                                    id="export-button",
                                    color="primary",
                                    style={"color": "white", "margin-right": "0px"}  # Increased margin between buttons
                                ),
                                width="auto"
                            ),
                            dbc.Col(
                                dbc.Button(
                                    [html.I(className="fas fa-exclamation-circle"), " Report an Issue"],  # Icon with the button text
                                    id="open-modal-button", n_clicks=0, color="danger", className="me-1",
                                    style={'display': 'none'},  # Hidden by default
                                ),
                                width="auto"
                            ),
                            dbc.Col(
                                dmc.Button(
                                    "Issues",
                                    leftSection=DashIconify(icon="mdi:git-issue", width=20),
                                    rightSection=None,  # Initially None, replaced by badge if necessary
                                    id="open-issues-button",
                                    n_clicks=0,
                                    style={'display': 'none', 'margin-right': "20px"},  # Hidden by default, increased margin
                                ),
                                width="auto"
                            ),
                            html.Div(id='onhold-count', style= {'display': 'none'}),
                        ],
                        align="center",
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
    color="#1B2131",
    className="mb-3",
)

    # Modal for editing data
    edit_modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Edit Data"),style={"background-color": "#1B2131"}),
            dbc.ModalBody(
                dash_table.DataTable(
                    id='edit-table',
                    columns=[{"name": i, "id": i} for i in ['unique_id', 'OFFICE', 'FISCAL_YEAR', 'MONTH', 'SURVEY_GROUP', 'SOLD_TO', 'GLOBAL_CUSTOMER', 'SOLD_TO_NAME', 'FIRST_NAME', 'LAST_NAME', 'EMAIL', 'OVERALL_SATISFACTION', 'CUSTOMER_SERVICE_REPRESENTATIVE_SATISFACTION', 'EASE_OF_DOING_BUSINESS', 'ADDITIONNAL_COMMENTS', 'CUSTOMER_SATISFACTION_INDEX']],
                    editable=True,
                    row_deletable=True,
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'color': 'black'},
                ),
                style={"maxHeight": "60vh", "overflowY": "auto","background-color": "#1B2131","border-top": "none"}
            ),
            dbc.ModalFooter(
                dbc.Button("Save Changes", id="save-changes", className="ml-auto", style={"background-color": "#00b4ef","border-color": "#00b4ef","color": "black"}),style={"background-color": "#1B2131","border-top": "none"}
            ),
        ],
        id="edit-modal",
        size="lg",
    )

    export_modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Export Data Options"),style={"background-color": "#1B2131"}),
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
                    ], style={"background-color": "#1B2131","border-top": "none"}
                ),
            dbc.ModalFooter(
                dbc.Button("Export", id="confirm-export", className="ml-auto", style={"background-color": "#00b4ef","border-color": "#00b4ef","color": "black"}), style={"background-color": "#1B2131","border-top": "none"}
            ),
        ],
        id="export-modal",
        size="lg",
        is_open=False
    )

    issue_modal= dbc.Modal(
        [
            dbc.ModalHeader("Report an Issue", style={"background-color": "#1B2131"}),
            dbc.ModalBody([
                dbc.Input(id="issue-text", placeholder="Describe the issue...", type="text"),
                html.Br(),
                dcc.Upload(
                    id='upload-image',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select a Screenshot')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    # Allow multiple files to be uploaded
                    multiple=False
                ),
                html.Div(id='output-image-upload'),
                dcc.Input(id='output-image-path', type='hidden')
            ],style={"background-color": "#1B2131"}),
            dbc.ModalFooter(
                dbc.Button("Submit", id="submit-issue-button", style={"background-color": "#00b4ef","border-color": "#00b4ef","color": "black"}), style={"background-color": "#1B2131"}
            ),
        ],
        id="issue-modal",
        is_open=False,
    )
    
    resolve_issue_modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Manage Issues"),style={"background-color": "#1B2131"}),
            dbc.ModalBody([
                # Section for Onhold Issues
                html.H4("On Hold Issues", style={"margin-top": "10px"}),
                html.Div(id='unresolved-issues'),
                html.Hr(),
                # Section for Resolved Issues
                html.H4("Resolved Issues", style={"margin-top": "10px"}),
                html.Div(id='resolved-issues'),
            ], style={"background-color": "#1B2131"}),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-issues-modal", className="ml-auto", style={"background-color": "#00b4ef","border-color": "#00b4ef","color": "black"}), style={"background-color": "#1B2131"}
            )
        ],
        id="resolve-issues-modal",
        is_open=False
    )
    from datetime import datetime
    current_year = datetime.now().year



    dashboard_layout = html.Div(
        style={'backgroundColor': '#131722', 'padding': '20px'},  # Set the background color and text color
        children=[
            navbar,  # Add the navbar with the logo
            sidebar,  # Add the sidebar
            logout_modal,
            # dcc.Location(id='url'),
            dcc.Store(id='nclicks-store'),
            html.Div(id='output-data-upload'),
            html.Div(id='monthly-message'),
            edit_modal,  # Add the edit modal
            dcc.Download(id="download-dataframe-xlsx"),
            export_modal,  # Add the export modal
            issue_modal,
            html.Div(id='submit-status'),
            resolve_issue_modal,
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
                                type='number',
                                className="rounded"
                            ),
                            width=2,
                            className="d-flex align-items-center justify-content-center"
                        ),

                    ]),
                    
                    dbc.Row([
                        dbc.Col([html.A([
                                            html.Img(src="/assets/image.png", height="20px", style={"margin-right": "5px"})
                                            ], 
                                            id="export-line", n_clicks=0),
                                            dcc.Graph(id='line-graph')], width=6),
                        dbc.Col([html.A([
                                            html.Img(src="/assets/image.png", height="20px", style={"margin-right": "5px"})
                                            ], id="export-bar", n_clicks=0), dcc.Graph(id='bar-graph')], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([html.A([
                                            html.Img(src="/assets/image.png", height="20px", style={"margin-right": "5px"})
                                            ], id="export-pie", n_clicks=0), dcc.Graph(id='pie-graph')], width=6),
                        dbc.Col([html.A([
                                            html.Img(src="/assets/image.png", height="20px", style={"margin-right": "5px"})
                                            ], id="export-treemap", n_clicks=0), dcc.Graph(id='treemap-graph')], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([html.A([
                                            html.Img(src="/assets/image.png", height="20px", style={"margin-right": "5px"})
                                            ], id="export-evolution-bar", n_clicks=0), dcc.Graph(id='bar-evolution-graph')], width=12),
                    ]),
                    dbc.Row([
                        dbc.Col(
                            [html.A([
                                            html.Img(src="/assets/image.png", height="20px", style={"margin-right": "5px"})
                                            ], id="export-comments", n_clicks=0),
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