# =============================================================
# scrapers/gmail_parser.py — Parser alertes email Leboncoin
# Parse les emails d'alerte reçus dans Gmail
# Sources : Leboncoin, La Centrale, Autoscout24 alertes
# =============================================================

import re
import json
import base64
from datetime import datetime, timedelta
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

SOURCE_ID  = "gmail_parser"
SOURCE_NOM = "Alertes Email"
FIABILITE  = 5

# Fichier token Gmail
TOKEN_FILE = Path(__file__).parent.parent / "token.json"

# Senders d'alertes reconnus
SENDERS_ALERTES = {
    # Leboncoin
    "alertes@leboncoin.fr"                        : "Leboncoin",
    "alerte@leboncoin.fr"                         : "Leboncoin",
    "noreply@leboncoin.fr"                        : "Leboncoin",
    "no-reply@leboncoin.fr"                       : "Leboncoin",
    "no.reply@leboncoin.fr"                        : "Leboncoin",
    "no.reply@leboncoin.fr"                       : "Leboncoin",
    "info@news.leboncoin.fr"                      : "Leboncoin",
    # La Centrale — expéditeurs confirmés
    "info@mail-alerte.lacentrale.fr"              : "La Centrale",
    "no-reply@info1.lacentrale.fr"                : "La Centrale",
    "alertes@lacentrale.fr"                       : "La Centrale",
    # Autoscout24 — expéditeur confirmé
    "savedsearches@notifications.autoscout24.com" : "Autoscout24",
    "alert@autoscout24.fr"                        : "Autoscout24",
    "no-reply@autoscout24.fr"                     : "Autoscout24",
    # Le Parking
    "alertes@leparking.fr"                        : "Le Parking",
    # Autosphere
    "contact@autosphere.fr"                       : "Autosphere",
    # Aramisauto
    "newsletters@content.aramisauto.com"          : "Aramisauto",
    # Spoticar (Stellantis) — expéditeurs confirmés
    "info@spoticar.stellantis.com"                : "Spoticar",
    "bounce.web.stellantis.com"                   : "Spoticar",  # domaine de routage
}


# Cache singleton — évite de réinitialiser le service à chaque appel
_GMAIL_SERVICE_CACHE = None

def _get_gmail_service():
    """Obtient le service Gmail (singleton — réutilisé entre les modèles)."""
    global _GMAIL_SERVICE_CACHE
    if _GMAIL_SERVICE_CACHE is not None:
        return _GMAIL_SERVICE_CACHE
    import os
    token_env = os.environ.get("GMAIL_TOKEN")
    if token_env:
        token_data = json.loads(token_env)
        creds = Credentials.from_authorized_user_info(token_data, ["https://www.googleapis.com/auth/gmail.readonly"])
    elif TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), ["https://www.googleapis.com/auth/gmail.readonly"])
    else:
        return None

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    _GMAIL_SERVICE_CACHE = build("gmail", "v1", credentials=creds)
    return _GMAIL_SERVICE_CACHE


def _decoder_body(message: dict) -> str:
    """Décode le corps d'un email Gmail."""
    payload = message.get("payload", {})

    def extraire_texte(part):
        body = part.get("body", {})
        data = body.get("data", "")
        if data:
            try:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
            except Exception:
                return ""
        # Récursion sur les parties
        for sub in part.get("parts", []):
            texte = extraire_texte(sub)
            if texte:
                return texte
        return ""

    return extraire_texte(payload)


def _parser_leboncoin(texte: str, html: str, source: str, modele_nom: str = "Break") -> list:
    """Parse un email d'alerte Leboncoin."""
    annonces = []

    # Leboncoin envoie des annonces dans un format structuré
    # Pattern : titre + prix + km + lien
    blocs = re.split(r'(?=https?://www\.leboncoin\.fr/(?:ad/|vi/))', texte)

    for bloc in blocs:
        if "leboncoin.fr/ad/" not in bloc:
            continue
        try:
            # URL
            url_m = re.search(r'(https?://www\.leboncoin\.fr/(?:ad/voitures/\d+|vi/\d+))', bloc)
            if not url_m:
                continue
            url = url_m.group(1)

            # Prix
            prix = None
            prix_m = re.search(r'(\d[\d\s]+)\s*€', bloc)
            if prix_m:
                prix = int(re.sub(r"\s", "", prix_m.group(1)))

            # Km
            km = None
            km_m = re.search(r'(\d[\d\s]+)\s*km', bloc, re.IGNORECASE)
            if km_m:
                km = int(re.sub(r"\s", "", km_m.group(1)))

            # Année
            annee = None
            annee_m = re.search(r'\b(202[0-9])\b', bloc)
            if annee_m:
                annee = int(annee_m.group(1))

            # Toit
            toit = "toit ouvrant" in bloc.lower() or "panoram" in bloc.lower()

            # Titre
            titre_m = re.search(r'(?:Mercedes|BMW)[^\n]{0,60}', bloc, re.IGNORECASE)
            titre = titre_m.group(0).strip() if titre_m else f"{modele_nom} {annee or '?'}"

            annonces.append({
                "source"           : f"Leboncoin (alerte)",
                "source_id"        : SOURCE_ID,
                "fiabilite_source" : FIABILITE,
                "titre"            : titre[:60],
                "vendeur"          : "Via alerte Leboncoin",
                "url"              : url,
                "prix"             : prix,
                "annee"            : annee,
                "km"               : km,
                "toit_ouvrant"     : True if toit else None,
                "garantie_mois"    : None,
                "premiere_main"    : None,
                "entretien_constructeur": None,
            })
        except Exception:
            continue

    return annonces


def _parser_spoticar(texte: str, source_nom: str) -> list:
    """Parse un email d'alerte Spoticar."""
    annonces = []
    # Spoticar envoie des liens du type /voitures-occasion/mercedes-...-{id}
    urls = re.findall(r'https?://www\.spoticar\.fr/voitures-occasion/[^\s<>"&]+', texte)
    for url in urls[:10]:
        try:
            prix_m  = re.search(r'(\d[\d\s]+)\s*€', texte)
            km_m    = re.search(r'(\d[\d\s]+)\s*km', texte, re.IGNORECASE)
            annee_m = re.search(r'(202[0-9])', texte)
            toit    = "toit ouvrant" in texte.lower() or "panoram" in texte.lower()
            prix    = int(re.sub(r'\s', '', prix_m.group(1))) if prix_m else None
            km      = int(re.sub(r'\s', '', km_m.group(1))) if km_m else None
            annee   = int(annee_m.group(1)) if annee_m else None
            if not prix:
                continue
            annonces.append({
                "source"                 : "Spoticar (alerte)",
                "source_id"              : SOURCE_ID,
                "fiabilite_source"       : FIABILITE,
                "titre"                  : f"C300e Break {annee or '?'} via alerte Spoticar",
                "vendeur"                : "Via alerte Spoticar",
                "url"                    : url,
                "prix"                   : prix,
                "annee"                  : annee,
                "km"                     : km,
                "toit_ouvrant"           : True if toit else None,
                "garantie_mois"          : None,
                "premiere_main"          : None,
                "entretien_constructeur" : None,
            })
        except Exception:
            continue
    return annonces


def _parser_leparking(texte: str, source_nom: str, modele_nom: str = "Break") -> list:
    """Parse un email d'alerte Le Parking."""
    annonces = []
    urls = re.findall(r'https?://www\.leparking\.fr/voiture-occasion/[^\s<>"&]+\.html', texte)
    for url in urls[:10]:
        try:
            prix_m  = re.search(r'(\d[\d\s]+)\s*€', texte)
            km_m    = re.search(r'(\d[\d\s]+)\s*km', texte, re.IGNORECASE)
            annee_m = re.search(r'(202[0-9])', texte)
            toit    = "toit ouvrant" in texte.lower() or "panoram" in texte.lower()
            prix    = int(re.sub(r'\s', '', prix_m.group(1))) if prix_m else None
            km      = int(re.sub(r'\s', '', km_m.group(1))) if km_m else None
            annee   = int(annee_m.group(1)) if annee_m else None
            if not prix:
                continue
            annonces.append({
                "source": f"Le Parking (alerte)", "source_id": SOURCE_ID,
                "fiabilite_source": FIABILITE,
                "titre": f"{modele_nom} {annee or '?'} via alerte Le Parking",
                "vendeur": "Via alerte Le Parking", "url": url,
                "prix": prix, "annee": annee, "km": km,
                "toit_ouvrant": True if toit else None,
                "garantie_mois": None, "premiere_main": None,
                "entretien_constructeur": None,
            })
        except Exception:
            continue
    return annonces


def _parser_aramisauto(texte: str, modele_nom: str = "Break") -> list:
    """
    Parse un email Aramisauto.
    Structure réelle : données en clair + URL tracking avant "Voir l'annonce"
    """
    annonces = []
    # Chercher le bloc annonce : URL suivie de "Voir l'annonce"
    # L URL a une espace trailing avant \r\n
    voir_pattern = re.compile(
        r'(https://click\.tech\.aramisauto\.com/\?qs=[^\r\n]+?)\s*\r?\n\s*Voir',
        re.IGNORECASE
    )
    voir_urls = [m.group(1).strip() for m in voir_pattern.finditer(texte)]

    if not voir_urls:
        return annonces

    # Chercher année + km : "2024 - 33361 km" ou "2024 - 33 361 km"
    annee_km_matches = list(re.finditer(
        r'(20\d{2})\s*[-–]\s*([\d\s]+)\s*km', texte, re.IGNORECASE
    ))

    # Prix : "41 799 &#x20AC;" ou "41 799 €"
    prix_matches = list(re.finditer(
        r'([\d][\d\s]+)\s*(?:&#x20AC;|€|&#xE2;)', texte
    ))

    # Titres véhicule
    titre_matches = list(re.finditer(
        r'((?:Mercedes|BMW|Audi|Volkswagen|Peugeot|Renault|Citroën|Ford|Toyota)[^\n]{5,80})',
        texte
    ))

    for i, url in enumerate(voir_urls):
        try:
            # Trouver année+km le plus proche avant cette URL
            url_pos = texte.find(url)
            annee, km = None, None
            for ak in reversed(annee_km_matches):
                if ak.start() < url_pos:
                    annee = int(ak.group(1))
                    km    = int(re.sub(r'\s', '', ak.group(2)))
                    break

            # Prix le plus proche avant l URL
            prix = None
            for pm in reversed(prix_matches):
                if pm.start() < url_pos:
                    try:
                        prix = int(re.sub(r'\s', '', pm.group(1)))
                        if 500 < prix < 200000:
                            break
                    except ValueError:
                        pass

            if not prix:
                continue

            # Titre le plus proche avant l URL
            titre = modele_nom
            for tm in reversed(titre_matches):
                if tm.start() < url_pos:
                    titre = tm.group(1).strip()
                    break

            toit = True if any(w in titre.lower() for w in ['toit', 'panoram', 'sunroof']) else None

            annonces.append({
                "source"                 : "Aramisauto (alerte)",
                "source_id"              : SOURCE_ID,
                "fiabilite_source"       : 7,
                "titre"                  : titre[:80],
                "vendeur"                : "Aramisauto",
                "url"                    : url,
                "prix"                   : prix,
                "annee"                  : annee,
                "km"                     : km,
                "toit_ouvrant"           : toit,
                "garantie_mois"          : 12,
                "premiere_main"          : None,
                "entretien_constructeur" : None,
            })
        except Exception:
            continue

    return annonces


def _parser_generique(texte: str, source_nom: str, modele_nom: str = "Break") -> list:
    """Parser générique pour autres sources d'alertes."""
    annonces = []

    # Chercher des URLs d'annonces + prix
    urls = re.findall(r'https?://[^\s<>"]+(?:voiture|annonce|auto|car)[^\s<>"]*', texte)
    for url in urls[:10]:
        prix_m = re.search(r'(\d[\d\s.]+)\s*€', texte)
        km_m   = re.search(r'(\d[\d\s.]+)\s*km', texte, re.IGNORECASE)
        annee_m = re.search(r'\b(202[0-9])\b', texte)

        prix  = int(re.sub(r'[\s.]', '', prix_m.group(1))) if prix_m else None
        km    = int(re.sub(r'[\s.]', '', km_m.group(1))) if km_m else None
        annee = int(annee_m.group(1)) if annee_m else None

        if not prix:
            continue

        annonces.append({
            "source"           : f"{source_nom} (alerte)",
            "source_id"        : SOURCE_ID,
            "fiabilite_source" : FIABILITE,
            "titre"            : f"C300e Break {annee or '?'} via alerte {source_nom}",
            "vendeur"          : f"Via alerte {source_nom}",
            "url"              : url,
            "prix"             : prix,
            "annee"            : annee,
            "km"               : km,
            "toit_ouvrant"     : None,
            "garantie_mois"    : None,
            "premiere_main"    : None,
            "entretien_constructeur": None,
        })

    return annonces



def _parser_autoscout24(texte: str, source_nom: str, modele_nom: str = "Break") -> list:
    """
    Parse un email d'alerte Autoscout24.
    Stratégie : découper le texte en segments entre chaque URL d'annonce.
    Chaque segment contient les données (prix, km, année) propres à cette annonce.
    """
    annonces = []
    url_matches = list(re.finditer(
        r'<?(https?://www\.autoscout24\.fr/offres/[^\s<>"&]+)>?', texte
    ))
    if not url_matches:
        return annonces

    # Ignorer les URLs dupliquées (AS24 répète l'URL après "Détails")
    urls_vues = set()
    url_uniques = []
    for um in url_matches:
        url = um.group(1).strip()
        if url not in urls_vues:
            urls_vues.add(url)
            url_uniques.append(um)
    url_matches = url_uniques

    for i, um in enumerate(url_matches):
        url = um.group(1).strip()
        # Bloc = texte entre cette URL et la suivante (ou fin)
        # On prend 50 chars avant l'URL (titre) + jusqu'à la prochaine URL
        # Bloc = texte APRÈS cette URL jusqu'à la prochaine
        debut_bloc = um.end()
        if i + 1 < len(url_matches):
            fin_bloc = url_matches[i + 1].start()
        else:
            fin_bloc = min(len(texte), um.end() + 600)
        bloc = texte[debut_bloc:fin_bloc]
        # Titre : lignes juste avant l'URL (nom du véhicule)
        avant_url = texte[max(0, um.start()-300):um.start()]

        try:
            # Prix : "€ 39 490" ou "39 490 €"
            prix = None
            # Prix : chercher sur une seule ligne pour éviter fusion avec km
            for ligne in bloc.split('\n'):
                if '€' not in ligne:
                    continue
                # "€ 39 490" ou "39 490 €"
                pm = re.search(r'€\s*([\d][\d ]+)', ligne) or re.search(r'([\d][\d ]+)\s*€', ligne)
                if pm:
                    try:
                        v = int(re.sub(r'\s', '', pm.group(1)))
                        if 500 < v < 150000:
                            prix = v
                            break
                    except ValueError:
                        pass
            if not prix:
                continue

            # Km + Année : "33 300 km, 11/2023"
            km, annee = None, None
            # Chercher km sur une ligne dédiée : "33 300 km, 11/2023"
            for ligne in bloc.split('\n'):
                ligne = ligne.strip()
                if 'km' not in ligne.lower():
                    continue
                ka = re.search(r'([\d][\d ]+)\s*km[,\s]+(?:\d{2}/)?(20\d{2}|199\d)', ligne, re.IGNORECASE)
                if ka:
                    try:
                        km    = int(re.sub(r'\s', '', ka.group(1)))
                        annee = int(ka.group(2))
                        break
                    except ValueError:
                        pass
                km_only = re.search(r'([\d][\d ]+)\s*km', ligne, re.IGNORECASE)
                if km_only:
                    try:
                        km = int(re.sub(r'\s', '', km_only.group(1)))
                        break
                    except ValueError:
                        pass
            if not annee:
                an_m = re.search(r'\b(20\d{2})\b', bloc)
                if an_m:
                    try: annee = int(an_m.group(1))
                    except: pass

            lignes = [l.strip() for l in avant_url.split('\n')
                      if l.strip() and len(l.strip()) > 3
                      and not l.strip().startswith('<')
                      and not l.strip().startswith('http')
                      and '€' not in l and 'km' not in l.lower()
                      and 'recherche' not in l.lower()]
            titre = lignes[-1] if lignes else f"{modele_nom} via alerte AS24"
            if len(titre) > 100:
                titre = f"{modele_nom} {annee or '?'} via alerte AS24"

            toit = "panoram" in url.lower() or "toit" in titre.lower()

            annonces.append({
                "source"                 : "Autoscout24 (alerte)",
                "source_id"              : SOURCE_ID,
                "fiabilite_source"       : FIABILITE,
                "titre"                  : titre[:80],
                "vendeur"                : "Via alerte Autoscout24",
                "url"                    : url,
                "prix"                   : prix,
                "annee"                  : annee,
                "km"                     : km,
                "toit_ouvrant"           : True if toit else None,
                "garantie_mois"          : None,
                "premiere_main"          : None,
                "entretien_constructeur" : None,
            })
        except Exception:
            continue

    return annonces


def _parser_lacentrale(texte: str, source_nom: str, modele_nom: str = "Break") -> list:
    """Parse un email d'alerte La Centrale — extraction par bloc autour de chaque URL."""
    annonces = []
    url_matches = list(re.finditer(
        r'https?://www\.lacentrale\.fr/auto-occasion-annonce-[^\s<>"&]+', texte
    ))
    for um in url_matches:
        url = um.group(0).strip()
        start = max(0, um.start() - 200)
        end   = min(len(texte), um.end() + 400)
        bloc  = texte[start:end]
        try:
            prix = None
            for ligne in bloc.split('\n'):
                if '€' not in ligne:
                    continue
                pm = re.search(r'([\d][\d ]+)\s*€', ligne) or re.search(r'€\s*([\d][\d ]+)', ligne)
                if pm:
                    try:
                        v = int(re.sub(r'\s', '', pm.group(1)))
                        if 500 < v < 150000:
                            prix = v
                            break
                    except ValueError:
                        pass
            if not prix:
                continue

            km, annee = None, None
            km_annee = re.search(r'([\d][\d\s]+)\s*km[,\s]+(?:\d{2}/)?(20\d{2}|199\d)', bloc, re.IGNORECASE)
            if km_annee:
                try:
                    km    = int(re.sub(r'\s', '', km_annee.group(1)))
                    annee = int(km_annee.group(2))
                except ValueError:
                    pass
            else:
                km_m = re.search(r'([\d][\d\s]+)\s*km', bloc, re.IGNORECASE)
                if km_m:
                    try: km = int(re.sub(r'\s', '', km_m.group(1)))
                    except ValueError: pass
                an_m = re.search(r'\b(20\d{2})\b', bloc)
                if an_m:
                    try: annee = int(an_m.group(1))
                    except ValueError: pass

            annonces.append({
                "source"                 : "La Centrale (alerte)",
                "source_id"              : SOURCE_ID,
                "fiabilite_source"       : FIABILITE,
                "titre"                  : f"{modele_nom} {annee or '?'} via alerte La Centrale",
                "vendeur"                : "Via alerte La Centrale",
                "url"                    : url,
                "prix"                   : prix,
                "annee"                  : annee,
                "km"                     : km,
                "toit_ouvrant"           : None,
                "garantie_mois"          : None,
                "premiere_main"          : None,
                "entretien_constructeur" : None,
            })
        except Exception:
            continue
    return annonces


def scraper(modele: dict = None) -> list:
    """
    Parse les emails d'alertes dans Gmail.
    Cherche les emails des dernières 48h des expéditeurs reconnus.
    """
    if not HAS_GOOGLE:
        print(f"  ⚠️  Gmail Parser — google-auth non disponible")
        return []

    criteres   = modele.get("criteres", {}) if modele else {}
    modele_nom = modele.get("nom", "Break") if modele else "Break"
    marque     = (criteres.get("marque") or "").lower()  # ex: "mercedes-benz", "bmw", "audi"
    annee_min  = criteres.get("annee_min", 2023)
    budget_max = criteres.get("budget_max", 42000)
    km_max     = criteres.get("km_max", 65000)

    annonces = []

    try:
        service = _get_gmail_service()
        if not service:
            print(f"  ⚠️  Gmail Parser — token non disponible")
            return []

        # Rechercher emails d'alertes des dernières 48h
        senders_query = " OR ".join([f"from:{s}" for s in SENDERS_ALERTES.keys()])
        # Aussi chercher par sujet pour capturer les alertes "Mes recherches"
        query = f"({senders_query}) newer_than:2d"

        result  = service.users().messages().list(userId="me", q=query, maxResults=20).execute()
        messages = result.get("messages", [])

        if not messages:
            print(f"  ℹ️  Gmail Parser — Aucun email d'alerte dans les 48h")
            return []

        print(f"  📧 Gmail Parser — {len(messages)} email(s) d'alerte trouvé(s)")

        for msg in messages:
            try:
                message = service.users().messages().get(
                    userId="me", id=msg["id"], format="full"
                ).execute()

                # Identifier l'expéditeur
                headers_email = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
                from_addr  = headers_email.get("From", "").lower()
                source_nom = next((v for k, v in SENDERS_ALERTES.items() if k in from_addr), None)

                if not source_nom:
                    continue

                # Décoder le corps
                texte = _decoder_body(message)
                html  = texte  # même contenu pour l'instant

                # Parser selon la source
                if "leboncoin" in from_addr:
                    nouvelles = _parser_leboncoin(texte, html, source_nom, modele_nom)
                elif "autoscout24" in from_addr:
                    nouvelles = _parser_autoscout24(texte, source_nom, modele_nom)
                elif "lacentrale" in from_addr:
                    nouvelles = _parser_lacentrale(texte, source_nom, modele_nom)
                elif "leparking" in from_addr:
                    nouvelles = _parser_leparking(texte, source_nom, modele_nom)
                elif "aramisauto" in from_addr:
                    nouvelles = _parser_aramisauto(texte, modele_nom)
                elif "spoticar" in from_addr or "stellantis" in from_addr:
                    nouvelles = _parser_spoticar(texte, source_nom)
                else:
                    nouvelles = _parser_generique(texte, source_nom, modele_nom)

                # Filtrer selon critères + marque
                for a in nouvelles:
                    if a.get("prix") and a["prix"] > budget_max:
                        continue
                    if a.get("km") and a["km"] > km_max:
                        continue
                    if a.get("annee") and a["annee"] < annee_min:
                        continue
                    # Filtre marque : vérifier que le titre contient la marque attendue
                    if marque:
                        titre_lower = (a.get("titre") or "").lower()
                        # Normaliser : mercedes-benz → mercedes
                        marque_simple = marque.split("-")[0].split(" ")[0]
                        if marque_simple and marque_simple not in titre_lower:
                            continue
                    annonces.append(a)

            except Exception as e:
                print(f"  ⚠️  Gmail Parser — Erreur email {msg['id']}: {e}")
                continue

    except Exception as e:
        print(f"❌ Gmail Parser — {e}")

    # Dédupliquer par URL
    seen  = set()
    dedup = []
    for a in annonces:
        if a["url"] not in seen:
            seen.add(a["url"])
            dedup.append(a)

    print(f"✅ Gmail Parser — {len(dedup)} annonces trouvées via alertes email")
    return dedup
