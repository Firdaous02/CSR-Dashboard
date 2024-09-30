import json
from flask import Flask, session, redirect, url_for, request, render_template, flash, send_from_directory, jsonify, send_file
from dash import Dash, html, dcc, Output, Input, dash, State, MATCH, ALL, no_update
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
from db import verify_user, add_issue, update_issue_status, get_issues, check_missing_months_in_db
from db import fetch_data
from db import insert_data
import plotly.express as px
import base64
import io
from io import BytesIO



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
            flash('Incorrect Credentials', 'danger')
    
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

    dcc.Interval(
        id='interval-component',
        interval=1000,  # 60 secondes
        n_intervals=0
    )
    
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
                                        html.Span("Resolved", className="badge badge-success", style={"color":"success"}),  # Badge pour les réclamations résolues
                                    ], style={"background-color": "#131722"}
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
                                        "background-color": "#131722"
                                    },
                                    className="img-fluid rounded-start"
                                ),
                                style={'position': 'relative', 'width': '100%',"background-color": "#131722"},
                                className="col-md-auto"
                            ) if image_url else None
                        ],
                        className="g-0 d-flex align-items-center",
                    )
                ], id={'type': 'issue-card', 'index': issue_id},
                style={"background-color": "#131722"},
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
                                    ], style={"background-color": "#131722"}
                                ),
                                style={"background-color": "#131722"},
                                className="col-md-auto"
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
                                        "background-color": "#131722"
                                        
                                    },
                                    className="img-fluid rounded-start"
                                ),
                                style={'position': 'relative', 'width': '100%',"background-color": "#131722"},
                                className="col-md-auto"
                            ) if image_url else None
                        ],
                        className="g-0 d-flex align-items-center",
                    )
                ], id={'type': 'issue-card', 'index': issue_id},
                style={"background-color": "#131722"},
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


@dash_app.callback(
    [Output('open-issues-button', 'style'),
    Output('open-modal-button', 'style'),
    Output('user-management-div', 'children'),
    Output('user-guide-div', 'children')
    ],
    [Input('url', 'pathname')]
)
def update_user_management_button(pathname):
    role = session.get('role')
    issues_button_style = {'display': 'none'}
    report_issue_button_style = {'display': 'none'}

    if role == 'admin':
        issues_button_style = {'display': 'inline-block'}
        # Ajoutez un lien qui redirige vers Flask
        return issues_button_style, report_issue_button_style, html.A(
            dbc.Button("User Management", id="user-management-button", className="mr-2", style={"background-color": "#00b4ef", "border-color": "#00b4ef", "color": "black" , "width": "100%"}),
            href='/user_management'  # Lien vers la route Flask
        ), html.A(
            dbc.Button("Admin Guide", id="user-guide-link", style={"background-color": "#00b4ef", "border-color": "#00b4ef", "color": "black", "width": "100%"}),
            href='/admin_guide'  # Lien vers la route Flask
        )
    elif role == 'user':
        report_issue_button_style = {'display': 'inline-block'}

        return issues_button_style, report_issue_button_style, '', html.A(
            dbc.Button("User Guide", id="user-guide-link", style={"background-color": "#00b4ef", "border-color": "#00b4ef", "color": "black", "width": "100%"}),
            href='/user_guide'  # Lien vers la route Flask
        )
    return ''



@dash_app.callback(
    [Output('upload-data', 'style'),
     Output('edit-button', 'style'),
     Output('monthly-message', 'children'),
     Output('monthly-message', 'style')
     ],
    [Input('url', 'pathname'),
    Input('interval-component', 'n_intervals')],
)
def check_privileges(pathname, n_intervals):
    # Récupérer les privilèges de la session Flask
    user_privileges = session.get('privileges', [])
    
    message = ''
    upload_style = {'display': 'none'}
    edit_style = {'display': 'none'}
    message_style = {'display': 'none'}
    
    # Vérifier les privilèges pour l'importation de données
    if 'Import Data' in user_privileges:
        upload_style = {'display': 'inline-block'}
        check = check_missing_months_in_db()
        if check:
            message_style = {'display': 'block'}
        message = html.Div(
            check, className='alert alert-danger')

    # Vérifier les privilèges pour l'édition des données
    if 'Edit Data' in user_privileges:
        edit_style = {'color': 'black', 'display': 'inline-block'}
    
    return upload_style, edit_style, message, message_style


@app.route('/user_management', methods=['GET'])
def user_management_search():
    print("Route '/user_management' reached")
    search_query = request.args.get('search', '').lower()
    print(f"Search query: '{search_query}'")

    # Transformation des tuples en dictionnaires
    users_tuples = get_all_users()
    users = [
        {
            'ID': user[0],
            'FIRST_NAME': user[1],
            'LAST_NAME': user[2],
            'ROLE': user[3],
            'EMAIL': user[4],
            'PASSWORD': user[5],
            'PRIVILEGES': user[6]
        }
        for user in users_tuples
    ]
    print("All users:", users)

    # Si une recherche est effectuée, filtrer les utilisateurs en fonction de la requête
    if search_query:
        filtered_users = [
            user for user in users if
            search_query in user['EMAIL'].lower() or
            search_query in user['FIRST_NAME'].lower() or
            search_query in user['LAST_NAME'].lower() or
            search_query in user['ROLE'].lower() or
            search_query in user['PRIVILEGES'].lower()
        ]
        print("Filtered users:", filtered_users)
    else:
        filtered_users = users

    return render_template('user_management.html', users=filtered_users, request=request)


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



@app.route('/test')
def test_route():
    return "Test route is working!"

# Page d'accueil qui redirige vers le login
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/admin_guide')
def admin_guide():
    return render_template('admin_guide.html')
@app.route('/user_guide')
def user_guide():
    return render_template('user_guide.html')

@app.route('/download-template')
def download_template():
    # Create an Excel file with only column headers
    output = BytesIO()  # A binary stream to hold the Excel file in memory

    # Define the column headers
    columns = ['OFFICE', 'FISCAL_YEAR', 'MONTH', 'SURVEY_GROUP', 'SOLD_TO', 'SOLD_TO_NAME', 'GLOBAL_CUSTOMER', 'FIRST_NAME','LAST_NAME','EMAIL','OVERALL_SATISFACTION','CUSTOMER_SERVICE_REPRESENTATIVE_SATISFACTION','EASE_OF_DOING_BUSINESS','CUSTOMER_SATISFACTION_INDEX']

    # Create an empty DataFrame with just the headers
    df = pd.DataFrame(columns=columns)

    # Write the DataFrame to an Excel file
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    
    # Set the position to the beginning of the stream
    output.seek(0)

    # Send the file to the user as an attachment
    return send_file(output, 
                     download_name="excel_template.xlsx", 
                     as_attachment=True, 
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == "__main__":
    app.run(debug=True)
