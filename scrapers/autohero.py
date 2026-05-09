# =============================================================
# scrapers/autohero.py — Scraper Autohero
# Autohero expose une API JSON propre — source la plus fiable
# Garantie 12 mois incluse sur tous leurs véhicules
# =============================================================

import httpx
from config import CRITERES

SOURCE_ID   = "autohero"
SOURCE_NOM  = "Autohero"
FIABILITE   = 10  # garantie 12 mois systématique

# URL de l'API Autohero (reverse-engineered de leur site)
API_URL = "https://www.autohero.com/api/v1/search"


def _construire_params() -> dict:
    """Construit les paramètres de recherche pour l'API Autohero."""
    return {
        "make"          : "mercedes-benz",
        "model"         : "c-klasse",
        "body_type"     : "estate",          # break
        "fuel_type"     : "electric_gasoline", # hybride rechargeable
        "first_registration_year_from": CRITERES["annee_min"],
        "price_to"      : CRITERES["budget_max"],
        "mileage_to"    : CRITERES["km_max"],
        "country"       : "FR",
        "language"      : "fr",
        "page_size"     : 50,
        "page"          : 1,
        "sort"          : "price_asc",
    }


def _normaliser_annonce(item: dict) -> dict:
    """Normalise une annonce Autohero au format standard du projet."""
    specs = item.get("specs", {})
    titre = (
        f"C300e Break {item.get('firstRegistrationYear', '?')} · "
        f"{item.get('mileage', '?')} km"
    )

    # Détection toit ouvrant dans les équipements
    equipements = [e.lower() for e in item.get("features", [])]
    toit = any("panorama" in e or "toit" in e or "sunroof" in e or "glassdach" in e
               for e in equipements)

    return {
        "source"              : SOURCE_NOM,
        "source_id"           : SOURCE_ID,
        "fiabilite_source"    : FIABILITE,
        "titre"               : titre,
        "vendeur"             : "Autohero",
        "url"                 : f"https://www.autohero.com/fr/auto/{item.get('id', '')}",
        "prix"                : item.get("price"),
        "annee"               : item.get("firstRegistrationYear"),
        "km"                  : item.get("mileage"),
        "puissance_ch"        : item.get("power"),
        "toit_ouvrant"        : toit if equipements else None,
        "garantie_mois"       : 12,           # systématique Autohero
        "premiere_main"       : None,
        "entretien_constructeur": None,
        "couleur"             : item.get("color"),
        "finition"            : item.get("trim"),
        "equipements_raw"     : item.get("features", []),
        "source_raw"          : item,
    }


def scraper() -> list:
    """
    Lance le scraping Autohero.
    Retourne une liste d'annonces normalisées.
    """
    annonces = []
    params   = _construire_params()

    try:
        headers = {
            "User-Agent"  : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept"      : "application/json",
            "Accept-Lang" : "fr-FR,fr;q=0.9",
        }

        with httpx.Client(timeout=15, follow_redirects=True) as client:
            resp = client.get(API_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("data", data.get("listings", data.get("results", [])))

        for item in items:
            try:
                annonce = _normaliser_annonce(item)
                # Filtrage strict
                if _est_eligible(annonce):
                    annonces.append(annonce)
            except Exception as e:
                print(f"  ⚠️  Autohero — Erreur normalisation item : {e}")

        print(f"✅ Autohero — {len(annonces)} annonces éligibles trouvées")

    except httpx.HTTPStatusError as e:
        print(f"❌ Autohero — Erreur HTTP {e.response.status_code}")
    except Exception as e:
        print(f"❌ Autohero — Erreur : {e}")

    return annonces


def _est_eligible(annonce: dict) -> bool:
    """Vérifie que l'annonce respecte les critères minimaux."""
    if annonce.get("annee") and annonce["annee"] < CRITERES["annee_min"]:
        return False
    if annonce.get("km") and annonce["km"] > CRITERES["km_max"]:
        return False
    if annonce.get("prix") and annonce["prix"] > CRITERES["budget_max"]:
        return False
    return True
