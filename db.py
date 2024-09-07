import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import text
import pandas as pd

# Connexion à la base de données
engine = create_engine('mssql+pyodbc://@localhost/CSIData?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes')
connection = engine.connect()

def verify_user(email, password):
    query = text("SELECT FIRST_NAME, LAST_NAME, ROLE FROM USERS WHERE EMAIL = :email AND PASSWORD = :password")
    result = connection.execute(query, {'email': email, 'password': password}).fetchone()
    
    if result:
        return {'first_name': result[0], 'last_name': result[1], 'role': result[2]}
    else:
        return None

def fetch_data(query):
    with engine.connect() as connection:
        return pd.read_sql(query, con=connection)


def insert_data(df, table_name, if_exists):
    with engine.connect() as connection:
        df.to_sql(table_name, con=connection, if_exists=if_exists, index=False)