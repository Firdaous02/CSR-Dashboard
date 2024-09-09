from flask import Flask, session, redirect, url_for, request, render_template, flash, send_from_directory
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dashboard import dashboard_layout
from callbacks import dashboard_callbacks
from db import verify_user
import os


# Initialiser l'application Flask
app = Flask(__name__)
app.secret_key = 'votre_cle_secrete'  # Nécessaire pour les sessions

# Utilisateurs factices (en réalité, vous utiliseriez une base de données)
users = {"admin": {"password": "password"}}

# Route de la page de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']  # L'utilisateur va entrer son email
        password = request.form['password']
        
        # Vérification des informations d'authentification via la base de données
        user = verify_user(email, password)
        
        if user:  # Si l'utilisateur est trouvé
            session['username'] = email  # Stocker l'email dans la session
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants incorrects.', 'danger')
    
    return render_template('login.html')

# Route protégée pour le tableau de bord Dash
@app.route('/dashboard')
def dashboard():
    if 'username' in session:  # Vérifier si l'utilisateur est connecté
        return redirect('/dash')
    else:
        flash('Veuillez vous connecter d\'abord.', 'warning')
        return redirect(url_for('login'))

# Route pour déconnexion
@app.route('/logout')
def logout():
    session.pop('username', None)  # Supprimer l'utilisateur de la session
    flash('Déconnecté avec succès.', 'success')
    return redirect(url_for('login'))

@app.route('/assets/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(os.getcwd(), 'assets'), filename)

# Créer une instance Dash en lui passant l'application Flask comme serveur
dash_app = Dash(__name__, server=app, url_base_pathname='/dash/', external_stylesheets=[dbc.themes.DARKLY, "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"], suppress_callback_exceptions=True)

# Créer la mise en page Dash
dash_app.layout = html.Div([
    dcc.Location(id="url-redirect", refresh=True),
    dashboard_layout,
    html.A("Se déconnecter", href="/logout")
])
dashboard_callbacks(dash_app)
# Page d'accueil qui redirige vers le login
@app.route('/')
def index():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
