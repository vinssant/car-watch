# =============================================================
# core/mailer.py — Envoi Gmail via API Google (OAuth2)
# Fonctionne en local et sur GitHub Actions
# =============================================================

import os
import base64
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# Google API
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


SCOPES      = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE  = Path(__file__).parent.parent / "token.json"


def _obtenir_service():
    """
    Obtient le service Gmail.
    
    En local    : lit token.json (généré par oauth_setup.py)
    GitHub Actions : lit la variable d'env GMAIL_TOKEN (secret GitHub)
    """
    creds = None

    # GitHub Actions : token en variable d'environnement
    token_env = os.environ.get("GMAIL_TOKEN")
    if token_env:
        token_data = json.loads(token_env)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    # Local : token.json
    elif TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # Rafraîchir si expiré
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Sauvegarder le token rafraîchi
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

    if not creds or not creds.valid:
        raise RuntimeError(
            "Token Gmail invalide. "
            "Lancez python oauth_setup.py pour configurer l'authentification."
        )

    return build("gmail", "v1", credentials=creds)


def envoyer_email(destinataire: str, sujet: str, corps_html: str, corps_texte: str = "") -> bool:
    """
    Envoie un email HTML via Gmail API.
    
    Retourne True si succès, False sinon.
    """
    try:
        service = _obtenir_service()

        message = MIMEMultipart("alternative")
        message["to"]      = destinataire
        message["subject"] = sujet

        # Version texte (fallback)
        if corps_texte:
            message.attach(MIMEText(corps_texte, "plain", "utf-8"))

        # Version HTML
        message.attach(MIMEText(corps_html, "html", "utf-8"))

        # Encodage
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        print(f"✅ Email envoyé à {destinataire} — Sujet : {sujet}")
        return True

    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")
        return False
