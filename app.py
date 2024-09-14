import json
from flask import Flask, session, redirect, url_for, request, render_template, flash, send_from_directory, jsonify
from dash import Dash, html, dcc, Output, Input, dash, State, MATCH, ALL
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from dashboard import dashboard_layout
from callbacks import dashboard_callbacks
from db import verify_user, count_onhold_issues
import os
from db import get_all_users, get_user_by_email, update_user_in_db, delete_user_from_db, add_user_db, insert_data, update_table
from werkzeug.security import generate_password_hash
import pandas as pd
from db import verify_user, add_issue, update_issue_status, get_issues
from db import fetch_data
from db import insert_data
import plotly.express as px
import base64
import io


# Initialiser l'application Flask
app = Flask(__name__)
app.secret_key = 'votre_cle_secrete'  # Nécessaire pour les sessions


# Route de la page de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']  # L'utilisateur va entrer son email
        password = request.form['password']
        
        
        # Vérification des informations d'authentification via la base de données
        user = verify_user(email, password)
        
        if user:  # Si l'utilisateur est trouvé
            session['id']= user['id']
            session['username'] = email  # Stocker l'email dans la session
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            session['role'] = user['role']
            session['privileges'] = user['privileges']
            print("User Role After Login:*", session.get('role'),"*")
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants incorrects.', 'danger')
    
    return render_template('login.html')

# Route protégée pour le tableau de bord Dash
@app.route('/dashboard')
def dashboard():
    if 'username' in session:  # Vérifier si l'utilisateur est connecté
        print("User Role in Dashboard Route:", session.get('role'))
        # privileges = session.get('privileges', '')
        # return render_template('dashboard.html')
        return redirect('/dash')
    else:
        flash('Veuillez vous connecter d\'abord.', 'warning')
        return redirect(url_for('login'))

# Route pour déconnexion
@app.route('/logout')
def logout():
    session.pop('username', None)  # Supprimer l'utilisateur de la session
    return redirect(url_for('login'))

@app.route('/assets/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(os.getcwd(), 'assets'), filename)

dash._dash_renderer._set_react_version('18.2.0')
# Créer une instance Dash en lui passant l'application Flask comme serveur
dash_app = Dash(__name__, server=app, url_base_pathname='/dash/', external_stylesheets=[dbc.themes.DARKLY, "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"], suppress_callback_exceptions=True)


# onhold_count = count_onhold_issues()

# Créer la mise en page Dash
dash_app.layout = dmc.MantineProvider(
    theme={"colorScheme": "light"},
    children=html.Div([
    dcc.Location(id="url-redirect", refresh=True),
    html.Div(id='page-content'),
    dashboard_layout(),
    # dcc.Store(id='user-privileges'),
     
    html.A("Se déconnecter", href="/logout"),
    dmc.Button(
        "GitHub",
        leftSection=DashIconify(icon="radix-icons:github-logo", width=20),
        rightSection=dmc.Badge("3", circle=True, color="gray"),
    ),
    dcc.Interval(
        id='interval-component',
        interval=1000,  # 60 secondes
        n_intervals=0
    )
    
    # dbc.Row(
    #     dbc.Col(html.Div(id='session-info'), width={"size": 6, "offset": 3}),
    # ),
    # dcc.Location(id='url', refresh=False),
])
)
dashboard_callbacks(dash_app)

# Callback to handle form submission
@dash_app.callback(
    Output('submit-status', 'children'),
    [Input('submit-issue-button', 'n_clicks')],
    [State('issue-text', 'value'), State('output-image-path', 'value')]
)
def submit_issue(n_clicks, text, image_path):
    print(f"n_clicks: {n_clicks}, text: {text}, image_path: {image_path}")
    if n_clicks and n_clicks > 0:

        user_id = session.get('id') 
        print(f"User ID: {user_id}")

        if not text:
            return html.Div(
                        "Please describe the issue.",
                        className='alert alert-danger'
                    )
            

        if not image_path:
            image_path = ''  # Utiliser un chemin vide par défaut si aucune image n'a été soumise
        
        # date = pd.Timestamp.now()  # Récupérer la date actuelle
        # Insérer les données dans la base
        data = {
            'user_id': [user_id],
            'text': [text],
            'status': ['onhold'],
            'screenshot_path': [image_path],
            # 'created_at': [date]
        }
        df = pd.DataFrame(data)
        insert_data(df, 'reclamations', 'append')
        return html.Div(
                        "Issue successfully submitted.",
                        className='alert alert-success'
                    )
        
    return ""

# Génération des cartes dynamiques
# def generate_issue_cards_from_db(status):
#     issues = get_issues(status)
#     print(issues)  # Récupérer les réclamations depuis la base de données
#     issue_cards = []

#     for issue in issues:
#         issue_id = issue[0]
#         issue_text = issue[1]
#         image_url = issue[2]
#         date = issue[3]
#         first_name = issue[4]
#         last_name = issue[5]

#         card = dbc.Card([
#             dbc.CardBody([
#                 html.H5(f"Issue {issue_id}"),
#                 html.P(issue_text),
#                 dbc.Button("Mark as resolved", id={'type': 'resolve-btn', 'index': issue_id}),
#             ]),
#         ], id={'type': 'issue-card', 'index': issue_id})  # ID dynamique pour chaque carte

#         issue_cards.append(card)

#     return issue_cards

def generate_issue_cards_from_db(status):
    issues = get_issues(status)
    issue_cards = []

    if not issues:
        return [html.P(f"No issues {status} available.", className="text-muted")]

    for issue in issues:
        issue_id = issue[0]
        issue_text = issue[1]
        image_url = issue[2]
        date = issue[3]
        first_name = issue[4]
        last_name = issue[5]

        # Si c'est une réclamation résolue
        if status == 'resolved':
            card = dbc.Card(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.CardBody(
                                    [
                                        html.H4(f"{first_name} {last_name}", className="card-title"),
                                        html.P(issue_text, className="card-text"),
                                        html.Small(f"{date}", className="card-text text-muted"),
                                        html.Br(),
                                        html.Span("Resolved", className="badge badge-success"),  # Badge pour les réclamations résolues
                                    ]
                                ),
                                className="col-md-auto",
                            ),
                            dbc.Col(
                                dbc.CardImg(
                                    src=image_url, top=True,
                                    style={
                                        'maxWidth': '200px', 
                                        'maxHeight': '200px',
                                        'position': 'absolute',
                                        'right': '0',
                                        'top': '10px',
                                        'transform': 'translateY(-110%)',
                                    },
                                    className="img-fluid rounded-start"
                                ),
                                style={'position': 'relative', 'width': '100%'},
                                className="col-md-auto"
                            ) if image_url else None
                        ],
                        className="g-0 d-flex align-items-center",
                    )
                ], id={'type': 'issue-card', 'index': issue_id},
                className="mb-3",
            )
        else:
            card = dbc.Card(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.CardBody(
                                    [
                                        html.H4(f"{first_name} {last_name}", className="card-title"),
                                        html.P(issue_text, className="card-text"),
                                        html.Small(f"{date}", className="card-text text-muted"),
                                        html.Br(),
                                        dbc.Button("Mark as Resolved", id={'type': 'resolve-btn', 'index': issue_id}, n_clicks=0, color="success")
                                    ]
                                ),
                                className="col-md-auto",
                            ),
                            dbc.Col(
                                dbc.CardImg(
                                    src=image_url, top=True,
                                    style={
                                        'maxWidth': '200px', 
                                        'maxHeight': '200px',
                                        'position': 'absolute',
                                        'right': '0',
                                        'top': '10px',
                                        'transform': 'translateY(-110%)',
                                    },
                                    className="img-fluid rounded-start"
                                ),
                                style={'position': 'relative', 'width': '100%'},
                                className="col-md-auto"
                            ) if image_url else None
                        ],
                        className="g-0 d-flex align-items-center",
                    )
                ], id={'type': 'issue-card', 'index': issue_id},
                className="mb-3",
            )
        
        issue_cards.append(card)
    
    return issue_cards


@dash_app.callback(
    [Output('onhold-count', 'children'),
     Output('unresolved-issues', 'children'),
     Output('resolved-issues', 'children'),
     Output('open-issues-button', 'rightSection')],
    [Input('interval-component', 'n_intervals')]
)
def update_display(n_intervals):
    onhold_count = count_onhold_issues()
    unresolved_issues = generate_issue_cards_from_db('onhold')
    resolved_issues = generate_issue_cards_from_db('resolved')
    
    badge = None
    if onhold_count > 0:
        badge = dmc.Badge(str(onhold_count), circle=True, color="red")

    return onhold_count, unresolved_issues, resolved_issues, badge


# Fonction pour marquer comme résolu
@dash_app.callback(
    Output({'type': 'issue-card', 'index': MATCH}, 'children'),
    Input({'type': 'resolve-btn', 'index': MATCH}, 'n_clicks'),
    State({'type': 'resolve-btn', 'index': MATCH}, 'id')
)
def mark_issue_resolved(n_clicks, button_id):
    if not n_clicks:
        return dash.no_update

    issue_id = button_id['index']
    update_issue_status(issue_id)  # Mettre à jour la réclamation en résolu

    # Retourne un message ou met à jour la carte après résolution
    return f"Issue {issue_id} marked as resolved"


# #session
# @dash_app.callback(
#     Output('session-info', 'children'),
#     [Input('url', 'pathname')]
# )
# def check_session(pathname):
#     # Vérifier la présence de la clé 'role' dans la session
#     role = session.get('role')
#     if role:
#         return f"Session Role: {role}"
#     else:
#         return "No session role found."

@dash_app.callback(
    Output('user-management-div', 'children'),
    [Input('url', 'pathname')]
)
def update_user_management_button(pathname):
    role = session.get('role')
    if role == 'admin':
        # Ajoutez un lien qui redirige vers Flask
        return html.A(
            dbc.Button("User Management", id="user-management-button", color='primary'),
            href='/user_management'  # Lien vers la route Flask
        )
    return ''



@dash_app.callback(
    [Output('upload-data', 'style'),
     Output('edit-button', 'style'),
     ],
    [Input('url', 'pathname')],
)
def check_privileges(pathname):
    # Récupérer les privilèges de la session Flask
    user_privileges = session.get('privileges', [])
    
    message = ""
    upload_style = {'display': 'none'}
    edit_style = {'display': 'none'}
    
    # Vérifier les privilèges pour l'importation de données
    if 'Import Data' in user_privileges:
        upload_style = {'display': 'inline-block'}

    # Vérifier les privilèges pour l'édition des données
    if 'Edit Data' in user_privileges:
        edit_style = {'color': 'black', 'display': 'inline-block'}
    
    return upload_style, edit_style

# @dash_app.callback(
#     [
#         Output('line-graph', 'figure'),
#         Output('bar-graph', 'figure'),
#         Output('pie-graph', 'figure'),
#         Output('treemap-graph', 'figure'),
#         Output('bar-evolution-graph', 'figure'),
#         Output('comments-table', 'data')  # Output to update the table

#     ],
#     [
#         Input('filter-dropdown', 'value'),
#         Input('fiscal-year-input-filter', 'value')
#     ]
# )

# def update_graphs(filter_value, fiscal_year):
#     user_privileges = session.get('privileges', [])

#     fiscal_year_query = f"((FISCAL_YEAR = '{fiscal_year - 1}' and MONTH in ('OCTOBER', 'NOVEMBER', 'DECEMBER') ) OR (FISCAL_YEAR= '{fiscal_year}' and MONTH in ('JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER')))"

#     #Pie graph
#     query_pie = f"SELECT OVERALL_SATISFACTION, COUNT(OVERALL_SATISFACTION) AS 'Rating'FROM DATA WHERE OVERALL_SATISFACTION IS NOT NULL AND {fiscal_year_query} GROUP BY OVERALL_SATISFACTION;"
#     df = fetch_data(query_pie)
#     custom_colors = ['#BE5B2D', '#D5692A', '#EB8204', '#FC9A22', '#FDB55E']
#     pie_fig = px.pie(df, names='OVERALL_SATISFACTION', values='Rating', title="Overall Satisfaction", color_discrete_sequence=custom_colors )
#     pie_fig.update_layout(
#         plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
#         paper_bgcolor='#0F2931',       # Light gray background for the entire chart
#         title_font=dict(size=20, color='white', family="Calibri"),  # Title font settings
#         legend_font=dict(color='white'),
#         font=dict(color='white')
#     )
    

#     #Tree map
#     query_treemap = f"SELECT GLOBAL_CUSTOMER, AVG(CUSTOMER_SATISFACTION_INDEX) 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} GROUP BY GLOBAL_CUSTOMER;"
#     df = fetch_data(query_treemap)
#     df['color'] = df['CSI'].apply(lambda x: '#429EBD' if x > 14 else 'red')
#     treemap_fig = px.treemap(df, path=['GLOBAL_CUSTOMER'], values='CSI',
#         color='color',  # Use the color column for coloring
#         color_discrete_map={'#429EBD': '#429EBD', 'red': 'red'},  # Define color mapping
#         title="Customer Satisfaction Index Treemap")
#     treemap_fig.update_layout(
#         plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
#         paper_bgcolor='#0F2931',       # Light gray background for the entire chart
#         title_font=dict(size=20,color='white', family="Calibri"),  # Title font settings
#         legend_font=dict(color='white'),
#         font=dict(color='black')
#     )
#         # Query for the comments
#     query_comments = f"SELECT OFFICE, FISCAL_YEAR, MONTH, GLOBAL_CUSTOMER, concat(FIRST_NAME, ' ',LAST_NAME) as name, ADDITIONNAL_COMMENTS from DATA WHERE ADDITIONNAL_COMMENTS is not null  AND {fiscal_year_query};"
#     comments_df = fetch_data(query_comments)

#     # Convert the DataFrame to a list of dictionaries for the DataTable
#     table_data = comments_df.to_dict('records')

#     if filter_value == 'global' and 'Filter by Global Customer' in user_privileges:
#         #Line graph BY GLOBAL CUSTOMER
#         query_line = f"SELECT GLOBAL_CUSTOMER, COUNT(CUSTOMER_SATISFACTION_INDEX) * 100.0 / COUNT(*) AS 'RES-RATE' FROM DATA WHERE {fiscal_year_query} GROUP BY GLOBAL_CUSTOMER;"

#         df = fetch_data(query_line)

#         line_fig = px.line(
#             df, 
#             x='GLOBAL_CUSTOMER', 
#             y='RES-RATE', 
#             labels={'RES-RATE': 'Response Rate (%)'},
#             title="Response Rate by Global Customer"
#         )
#         line_fig.update_layout(
#             xaxis_title='',  # Remove the x-axis label 
#             plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
#             paper_bgcolor='#0F2931',       # Light gray background for the entire chart
#             title_font=dict(size=20,color='white', family="Calibri"),  # Title font settings
#             legend_font=dict(color='white'),
#             font=dict(color='white')
#         )

#         #Bar graph BY GLOBAL CUSTOMER
#         query_bar = f"SELECT GLOBAL_CUSTOMER, AVG(CUSTOMER_SATISFACTION_INDEX) 'CSI Average' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} GROUP BY GLOBAL_CUSTOMER;"
#         df = fetch_data(query_bar)

#         df['color'] = df['CSI Average'].apply(lambda x: '#429EBD' if x > 14 else 'red')

#         bar_fig = px.bar(df, 
#             x='GLOBAL_CUSTOMER', 
#             y='CSI Average', 
#             color='color',  # Use the color column for coloring
#             color_discrete_map={'#429EBD': '#429EBD', 'red': 'red'},  # Define color mapping
#             title="Customer Satisfaction Index by Global Customer"
#         )
#         bar_fig.for_each_trace(lambda t: t.update(name='> 14' if t.name == 'blue' else '<= 14'))

#         bar_fig.update_layout(
#             xaxis_title='',  # Remove the x-axis label 
#             plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
#             paper_bgcolor='#0F2931',       # Light gray background for the entire chart
#             title_font=dict(size=20,color='white', family="Calibri"),  # Title font settings
#             legend_font=dict(color='white'),
#             font=dict(color='white')
#         )
#         #Evolution bar graph BY GLOBAL CUSTOMER
#         query_bar = f"SELECT MONTH, GLOBAL_CUSTOMER, AVG(CUSTOMER_SATISFACTION_INDEX) AS 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX IS NOT NULL AND {fiscal_year_query} GROUP BY GLOBAL_CUSTOMER, MONTH ORDER BY MONTH;"
#         df = fetch_data(query_bar)

#         df['color'] = df['CSI'].apply(lambda x: 'blue' if x > 14 else 'red')

#         bar_evolution_fig = px.bar(df, 
#             x='MONTH', 
#             y='CSI', 
#             color='GLOBAL_CUSTOMER',  # Use the color column for coloring
#             color_discrete_map={'blue': 'blue', 'red': 'red'},  # Define color mapping
#             barmode='group',
#             title="Customer Satisfaction Index by Global Customer"
#         )
#         bar_evolution_fig.update_layout(
#             xaxis_title='',
#             yaxis_title='Customer Satisfaction Index',
#             legend_title='Global Customer',
#             xaxis_tickangle=-45,
#             bargap=0.05,
#             plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
#             paper_bgcolor='#0F2931',       # Light gray background for the entire chart
#             title_font=dict(size=20,color='white', family="Calibri"),  # Title font settings
#             legend_font=dict(color='white'),
#             font=dict(color='white')
#         )
#     elif filter_value == 'ship_to' and 'Filter by Ship to' in user_privileges:
#         #Line graph
#         query_line = f"SELECT SOLD_TO_NAME, COUNT(CUSTOMER_SATISFACTION_INDEX) * 100.0 / COUNT(*) AS 'RES-RATE' FROM DATA WHERE {fiscal_year_query} GROUP BY SOLD_TO_NAME;"
#         df = fetch_data(query_line)
#         line_fig = px.line(
#             df, 
#             x='SOLD_TO_NAME', 
#             y='RES-RATE', 
#             labels={'RES-RATE': 'Response Rate (%)'},
#             title="Response Rate by Ship To"
#         )
#         line_fig.update_layout(
#             xaxis_title='',  # Remove the x-axis label 
#         )

#         #Bar graph
#         query_bar = f"SELECT SOLD_TO_NAME, AVG(CUSTOMER_SATISFACTION_INDEX) 'CSI Average' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} GROUP BY SOLD_TO_NAME;"
#         df = fetch_data(query_bar)
#         df['color'] = df['CSI Average'].apply(lambda x: 'blue' if x > 14 else 'red')

#         bar_fig = px.bar(df, 
#             x='SOLD_TO_NAME', 
#             y='CSI Average', 
#             color='color', 
#             color_discrete_map={'blue': 'blue', 'red': 'red'}, 
#             title="Customer Satisfaction Index Average by Ship To"
#         )
#         bar_fig.for_each_trace(lambda t: t.update(name='> 14' if t.name == 'blue' else '<= 14'))

#         bar_fig.update_layout(
#             xaxis_title='',  # Remove the x-axis label
#             yaxis_title='CSI Average',
#             legend_title='Color',
#             xaxis_tickangle=-45,
#             bargap=0.05,
#             plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
#             paper_bgcolor='#0F2931',       # Light gray background for the entire chart
#             title_font=dict(size=20,color='white', family="Calibri"),  # Title font settings
#             legend_font=dict(color='white'),
#             font=dict(color='white')
#         )
        
#         #Evolution bar graph
#         query_bar = f"SELECT MONTH, SOLD_TO_NAME, CUSTOMER_SATISFACTION_INDEX 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} ORDER BY MONTH;"
#         df = fetch_data(query_bar)
#         bar_evolution_fig = px.bar(df, 
#             x='MONTH', 
#             y='CSI', 
#             color='SOLD_TO_NAME',  # Use the color column for coloring
#             barmode='group',
#             title="Customer Satisfaction Index by Ship To"
#         )
#         bar_evolution_fig.update_layout(
#             xaxis_title='Month',
#             yaxis_title='Customer Satisfaction Index',
#             legend_title='Ship To',
#             xaxis_tickangle=-45,
#             bargap=0.05,
#             plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area background
#             paper_bgcolor='#0F2931',       # Light gray background for the entire chart
#             title_font=dict(size=20,color='white', family="Calibri"),  # Title font settings
#             legend_font=dict(color='white'),
#             font=dict(color='white')  
#         ) 
#     elif filter_value == 'office' and 'Filter by Office' in user_privileges:
#         #Line graph BY OFFICE
#         query_line = f"SELECT OFFICE, MONTH, COUNT(CUSTOMER_SATISFACTION_INDEX) * 100.0 / COUNT(*) AS 'RES-RATE' FROM DATA WHERE {fiscal_year_query} GROUP BY MONTH, OFFICE ORDER BY MONTH, OFFICE;"
#         df = fetch_data(query_line)
#         line_fig = px.line(
#             df, 
#             x='MONTH', 
#             y='RES-RATE', 
#             color='OFFICE',
#             labels={'RES-RATE': 'Response Rate (%)'},
#             title="Response Rate by Office"
#         )
#         line_fig.update_layout(
#             xaxis_title='',  # Remove the x-axis label 
#             legend_title='Office'
#         )

#         #Bar graph BY OFFICE
#         query_bar = f"SELECT OFFICE, AVG(CUSTOMER_SATISFACTION_INDEX) 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX is not null and {fiscal_year_query} GROUP BY OFFICE;"
#         df = fetch_data(query_bar)
#         df['color'] = df['CSI'].apply(lambda x: 'blue' if x > 14 else 'red')

#         bar_fig = px.bar(df, 
#             x='OFFICE', 
#             y='CSI', 
#             color='color', 
#             color_discrete_map={'blue': 'blue', 'red': 'red'}, 
#             title="Customer Satisfaction Index Average by Office"
#         )
#         bar_fig.for_each_trace(lambda t: t.update(name='> 14' if t.name == 'blue' else '<= 14'))

#         bar_fig.update_layout(
#             xaxis_title='',  # Remove the x-axis label
#             yaxis_title='CSI',
#             legend_title='Color',
#             xaxis_tickangle=-45,
#             bargap=0.05  
#         )
        
#         #Evolution bar graph BY OFFICE
#         query_bar = f"SELECT MONTH, OFFICE, AVG(CUSTOMER_SATISFACTION_INDEX) AS 'CSI' FROM DATA WHERE CUSTOMER_SATISFACTION_INDEX IS NOT NULL AND {fiscal_year_query} GROUP BY OFFICE, MONTH ORDER BY MONTH;"
#         df = fetch_data(query_bar)
#         bar_evolution_fig = px.bar(df, 
#             x='MONTH', 
#             y='CSI', 
#             color='OFFICE',  # Use the color column for coloring
#             barmode='group',
#             title="Customer Satisfaction Index by Office"
#         )
#         bar_evolution_fig.update_layout(
#             xaxis_title='Month',
#             yaxis_title='Customer Satisfaction Index',
#             legend_title='Office',
#             xaxis_tickangle=-45,
#             bargap=0.05  
#         )    

#     return line_fig, bar_fig, pie_fig, treemap_fig, bar_evolution_fig, table_data


#############################################################################################################################
#############################################################################################################################

# def get_dropdown_options():
#     user_privileges = session.get('privileges', [])
    
#     options = []
#     if 'Filter by Global Customer' in user_privileges:
#         options.append({'label': 'By Global Customer', 'value': 'global'})
#     if 'Filter by Ship to' in user_privileges:
#         options.append({'label': 'By Ship to', 'value': 'ship_to'})
#     if 'Filter by Office' in user_privileges:
#         options.append({'label': 'By Office', 'value': 'office'})

#     return options

# Callback pour mettre à jour les options du dropdown
# def update_dropdown_options():
#     user_privileges = session.get('privileges', [])
#     print("User Privileges:", user_privileges)  # Debug print

#     options = []

#     if 'Filter by Global Customer' in user_privileges:
#         options.append({'label': 'By Global Customer', 'value': 'global'})
    
#     if 'Filter by Ship to' in user_privileges:
#         options.append({'label': 'By Ship to', 'value': 'ship_to'})
    
#     if 'Filter by Office' in user_privileges:
#         options.append({'label': 'By Office', 'value': 'office'})

#     print("Dropdown Options:", options)  # Debug print
#     return options

# @dash_app.callback(
#     Output('filter-dropdown', 'options'),
#     [Input('url', 'pathname')]
# )
# def update_dropdown(pathname):
#     try:
#         options = update_dropdown_options()
#         print("Dropdown Options:", options)

#         return options
#     except Exception as e:
#         print("Error in update_dropdown:", e)  # Log error
#         return []

###############################################################################################################################

##################################################################################
# @dash_app.callback(
#     Output('url', 'href'),
#     [Input('user-management-button', 'n_clicks')]
# )

# def redirect_to_user_management(n_clicks):
#     if n_clicks:
#         return '/user_management'  # URL de la page user_management
#     return dash.no_update

@app.route('/user_management')
def user_management():
    if session.get('role') != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('user_management.html', users=get_all_users())

@app.route('/edit_user/<email>', methods=['GET', 'POST'])
def edit_user(email):
    user = get_user_by_email(email)  # Fonction pour récupérer les infos de l'utilisateur à partir de son email
    
    # Convertir les privilèges en liste si nécessaire
    privileges_list = user.PRIVILEGES.split(',') if isinstance(user.PRIVILEGES, str) else []
    
    if request.method == 'POST':
        # Récupérer les nouvelles informations du formulaire
        updated_email = request.form['email']
        updated_first_name = request.form['first_name']
        updated_last_name = request.form['last_name']
        updated_role = request.form['role']
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        updated_privileges = request.form.getlist('privileges')  # Récupérer la liste des privilèges cochés
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('edit_user', email=email))

        update_user_in_db(email, updated_email, updated_first_name, updated_last_name, updated_role, password, updated_privileges)
        flash('User updated successfully.', 'success')
        return redirect(url_for('user_management'))

    return render_template('edit_user.html', user=user, privileges_list=privileges_list)



        


@app.route('/delete_user/<email>', methods=['POST'])
def delete_user(email):
    message = delete_user_from_db(email)
    
    # Afficher un message à l'utilisateur
    flash(message, 'success' if 'success' in message else 'danger')
    
    # Rediriger vers la page de gestion des utilisateurs
    return redirect(url_for('user_management'))

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        privileges = request.form.getlist('privileges')

        # Vérifier que les deux mots de passe correspondent
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('add_user'))
        

        # Préparer les données pour l'insertion
        data = {
            'EMAIL': [email],
            'FIRST_NAME': [first_name],
            'LAST_NAME': [last_name],
            'ROLE': [role],
            'PASSWORD': [password],
            'PRIVILEGES': [','.join(privileges)]  # Joindre les privilèges avec une virgule
        }

        df = pd.DataFrame(data)

        # Insérer les données dans la base de données
        try:
            insert_data(df, 'USERS','append')
            flash('User added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding user: {e}', 'danger')
        
        return redirect(url_for('user_management'))
    
    return render_template('add_user.html')



# Page d'accueil qui redirige vers le login
@app.route('/')
def index():
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
