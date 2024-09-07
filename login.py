import dash_bootstrap_components as dbc
from dash import html

def login_form():
    return dbc.Row(
        dbc.Col(
            html.Div(
                [
                    html.H2("Login"),
                    dbc.Input(id="email-input", placeholder="Enter your email", type="email"),
                    dbc.Input(id="password-input", placeholder="Enter your password", type="password", className="mt-2"),
                    dbc.Button("Login", id="login-button", color="primary", className="mt-3"),
                    html.Div(id="login-message", className="mt-2")
                ]
            ),
            width=4, className="offset-md-4"
        )
    )
