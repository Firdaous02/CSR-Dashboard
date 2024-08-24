# Utiliser une image de base Python officielle
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements.txt dans le conteneur
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application dans le conteneur
COPY . .

# Exposer le port sur lequel l'application s'exécute
EXPOSE 5000

# Définir la commande par défaut pour démarrer l'application
CMD ["python", "app.py"]
