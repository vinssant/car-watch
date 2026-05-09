# =============================================================
# oauth_setup.py — Configuration OAuth2 Gmail
# À lancer UNE SEULE FOIS en local pour générer token.json
# =============================================================
#
# PRÉREQUIS :
# 1. Aller sur https://console.cloud.google.com
# 2. Créer un projet (ex: "mercedes-veille")
# 3. Activer l'API Gmail
# 4. Créer des identifiants OAuth2 > Application de bureau
# 5. Télécharger le JSON → le renommer "credentials.json"
#    et le placer dans ce dossier
# 6. Lancer : python oauth_setup.py
# 7. Copier le contenu de token.json → GitHub Secret "GMAIL_TOKEN"
# =============================================================

import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES           = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = Path("credentials.json")
TOKEN_FILE       = Path("token.json")


def main():
    if not CREDENTIALS_FILE.exists():
        print("❌ credentials.json introuvable.")
        print("   Téléchargez-le depuis Google Cloud Console → Identifiants → OAuth 2.0")
        return

    print("🔐 Démarrage du flux OAuth2 Gmail...")
    print("   Votre navigateur va s'ouvrir pour autoriser l'accès.")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES
    )
    creds = flow.run_local_server(port=0)

    # Sauvegarder le token
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print(f"✅ Token sauvegardé dans {TOKEN_FILE}")
    print()
    print("📋 ÉTAPE SUIVANTE — Ajouter à GitHub Secrets :")
    print("   1. Aller sur votre repo GitHub → Settings → Secrets → Actions")
    print("   2. New repository secret → Nom : GMAIL_TOKEN")
    print("   3. Valeur : coller le contenu ci-dessous")
    print()
    print("─" * 50)
    with open(TOKEN_FILE) as f:
        content = json.load(f)
    print(json.dumps(content, indent=2))
    print("─" * 50)
    print()
    print("⚠️  NE JAMAIS committer token.json ni credentials.json sur Git !")
    print("   Ils sont dans .gitignore pour cette raison.")


if __name__ == "__main__":
    main()
