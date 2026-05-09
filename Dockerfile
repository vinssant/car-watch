FROM python:3.11-slim

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code du projet
COPY . .

# Créer le dossier data s'il n'existe pas
RUN mkdir -p data reports

# Par défaut : lancer la veille
CMD ["python3", "main.py"]
