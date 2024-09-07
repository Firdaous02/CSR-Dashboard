from dash import Input, Output, State, dcc, html, no_update
from flask import session
from db import verify_user

def register_callbacks(app):
    @app.callback(
        [Output('login-message', 'children'),
         Output('url', 'pathname')],
        [Input('login-button', 'n_clicks')],
        [State('email-input', 'value'), State('password-input', 'value')]
    )
    def verify_login(n_clicks, email, password):
        if n_clicks is None:
            return "", no_update

        if not email or not password:
            return html.Div(
                "Please enter both email and password.",
                className='alert alert-danger'
            ), no_update

        # Appeler la fonction de vérification depuis le fichier db.py
        user = verify_user(email, password)
        if user:
            session['authenticated'] = True  # Stocker l'état d'authentification dans la session
            return "Redirecting...", "/dashboard"
        else:
            return html.Div(
                f'Invalid email or password. Please try again.',
                className='alert alert-danger'
            ), no_update
