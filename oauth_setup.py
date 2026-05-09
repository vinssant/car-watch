import json, os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES           = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = Path("credentials.json")
TOKEN_FILE       = Path("token.json")

def main():
    if not CREDENTIALS_FILE.exists():
        print("credentials.json introuvable")
        return

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )

    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline"
    )

    print()
    print("=" * 65)
    print("ETAPE 1 — Copiez cette URL dans votre navigateur :")
    print("=" * 65)
    print()
    print(auth_url)
    print()
    print("=" * 65)
    print()
    print("ETAPE 2 — Connectez-vous avec vinssant@gmail.com")
    print("          Autorisez l'acces -> Google affiche un CODE")
    print()
    code = input("ETAPE 3 — Collez le code ici : ").strip()

    flow.fetch_token(code=code)
    creds = flow.credentials

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print()
    print("token.json cree !")
    print()
    print("Copiez ce contenu dans GitHub Secret GMAIL_TOKEN :")
    print("=" * 65)
    with open(TOKEN_FILE) as f:
        content = json.load(f)
    print(json.dumps(content, indent=2))
    print("=" * 65)

if __name__ == "__main__":
    main()
