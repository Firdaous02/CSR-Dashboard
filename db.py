import sqlalchemy
from sqlalchemy import create_engine, Table, MetaData, update
from sqlalchemy import text
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from flask import flash



# Connexion à la base de données
engine = create_engine('mssql+pyodbc://@localhost/CSIData?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes')
connection = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()

def verify_user(email, password):
    query = text("SELECT ID, FIRST_NAME, LAST_NAME, ROLE , PRIVILEGES FROM USERS WHERE EMAIL = :email AND PASSWORD = :password")
    result = connection.execute(query, {'email': email, 'password': password}).fetchone()
    
    if result:
        return {'id': result[0], 'first_name': result[1], 'last_name': result[2], 'role': result[3], 'privileges': result[4]}
    else:
        return None

def fetch_data(query):
    with engine.connect() as connection:
        return pd.read_sql(query, con=connection)


def insert_data(df, table_name, if_exists):
    with engine.connect() as connection:
        df.to_sql(table_name, con=connection, if_exists=if_exists, index=False)

def update_table(df, table_name, key_column):
    # Charger les métadonnées et la table
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)
    
    with engine.connect() as connection:
        for index, row in df.iterrows():
            stmt = (
                update(table).
                where(table.c[key_column] == row[key_column]).
                values(row.to_dict())
            )
            connection.execute(stmt)

def get_all_users():
    with engine.connect() as connection:
        query = text("SELECT * FROM USERS")
        result = connection.execute(query).fetchall()
        
    return result

def get_user_by_email(email):
    try:
        # Créer la requête SQL
        query = text("SELECT * FROM users WHERE email = :email")
        result = connection.execute(query, {'email': email})
        
        user = result.fetchone()
        return user
    except Exception as e:
        print(f"Error fetching user by email: {e}")
        return None

def update_user_in_db(email, updated_email, first_name, last_name, role, password, privileges):
    try:
        # Créer la requête d'update
        query = text("""
            UPDATE users
            SET email = :updated_email, first_name = :first_name, last_name = :last_name, role = :role, password = :password, privileges = :privileges
            WHERE email = :email
        """)
        
        # Convertir la liste des privilèges en chaîne de caractères (vérifier le format attendu)
        privileges_str = ','.join(privileges)  # Ou utilisez JSON si nécessaire
        

        # Exécuter la requête d'update
        session.execute(query, {
            'updated_email': updated_email,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            'password': password,  # Stocker le mot de passe haché
            'privileges': privileges_str,
            'email': email
        })
        session.commit()  # Valider la transaction
        print("User updated successfully.")
        
    except Exception as e:
        session.rollback()  # Annuler en cas d'erreur
        print(f"Error updating user: {e}")
    finally:
        session.close()  # Toujours fermer la session après utilisation

# def update_user_in_db(email, updated_email, first_name, last_name, role, password, privileges):
#     try:
#         # Créer la requête d'update
#         query = text("""
#             UPDATE users
#             SET email = :updated_email, first_name = :first_name, last_name = :last_name, role = :role, password = :password, privileges = :privileges
#             WHERE email = :email
#         """)
#         privileges_str = ','.join(privileges)  # Convertir la liste des privilèges en chaîne de caractères

#         # Exécuter la requête d'update
#         connection.execute(query, {
#             'updated_email': updated_email,
#             'first_name': first_name,
#             'last_name': last_name,
#             'role': role,
#             'password': password,
#             'privileges': privileges_str,
#             'email': email
#         })

#         print("User updated successfully.")
#     except Exception as e:
#         print(f"Error updating user: {e}")


def delete_user_from_db(email):
    session = Session()
    try:
        # Requête de suppression utilisant SQLAlchemy avec des paramètres nommés
        query = text("DELETE FROM USERS WHERE EMAIL = :email")
        session.execute(query, {'email': email})  # Paramètre sous forme de dictionnaire
        session.commit()  # Appliquer les changements dans la base de données
        return "User deleted successfully."
    except Exception as e:
        session.rollback()  # En cas d'erreur, on annule la transaction
        return f"Error deleting user: {e}"
    finally:
        session.close()  # Fermer la session

def add_user_db(email, first_name, last_name, role, hashed_password, privileges):
    session = Session()
    try:
        query = text("""
            INSERT INTO USERS (EMAIL, FIRST_NAME, LAST_NAME, ROLE, PASSWORD, PRIVILEGES)
            VALUES (:email, :first_name, :last_name, :role, :password, :privileges)
        """)
        privileges_str = ','.join(privileges)

        # Exécuter la requête
        connection.execute(query, {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            'privileges': privileges_str,
            'password': hashed_password
        })

        # Vérifier que les changements sont commités
        session.commit()
        print("Transaction committed.")  # Debugging

        # Fermer la connexion
        connection.close()
        print(f"User {email} added successfully!")
        return "User added successfully!"

    except IntegrityError as e:
        session.rollback()
        print(f"IntegrityError: {e}")
        return f"Error adding user: {e}"

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        return f"An error occurred: {str(e)}"

    finally:
        session.close()



