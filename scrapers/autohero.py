# =============================================================
# scrapers/autohero.py — Scraper Autohero
# Garantie 12 mois incluse sur tous leurs véhicules
# =============================================================

import httpx

SOURCE_ID  = "autohero"
SOURCE_NOM = "Autohero"
FIABILITE  = 10

API_URL = "https://www.autohero.com/api/v1/search"

HEADERS = {
    "User-Agent"  : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept"      : "application/json",
    "Accept-Lang" : "fr-FR,fr;q=0.9",
}


def _construire_params(criteres: dict) -> dict:
    return {
        "make"          : "mercedes-benz",
        "model"         : "c-klasse",
        "body_type"     : "estate",
        "fuel_type"     : "electric_gasoline",
        "first_registration_year_from": criteres.get("annee_min", 2023),
        "price_to"      : criteres.get("budget_max", 42000),
        "mileage_to"    : criteres.get("km_max", 65000),
        "country"       : "FR",
        "language"      : "fr",
        "page_size"     : 50,
        "page"          : 1,
        "sort"          : "price_asc",
    }


def _normaliser_annonce(item: dict) -> dict:
    annee  = item.get("firstRegistrationYear")
    km     = item.get("mileage")
    titre  = f"C300e Break {annee or '?'} · {km or '?'} km"
    equips = [str(e).lower() for e in item.get("features", [])]
    toit   = any("panorama" in e or "toit" in e or "sunroof" in e for e in equips) if equips else None

    return {
        "source"              : SOURCE_NOM,
        "source_id"           : SOURCE_ID,
        "fiabilite_source"    : FIABILITE,
        "titre"               : titre,
        "vendeur"             : "Autohero",
        "url"                 : f"https://www.autohero.com/fr/auto/{item.get('id', '')}",
        "prix"                : item.get("price"),
        "annee"               : annee,
        "km"                  : km,
        "puissance_ch"        : item.get("power"),
        "toit_ouvrant"        : toit,
        "garantie_mois"       : 12,
        "premiere_main"       : None,
        "entretien_constructeur": None,
        "couleur"             : item.get("color"),
        "finition"            : item.get("trim"),
    }


def _est_eligible(annonce: dict, criteres: dict) -> bool:
    if annonce.get("annee") and annonce["annee"] < criteres.get("annee_min", 2023):
        return False
    if annonce.get("km") and annonce["km"] > criteres.get("km_max", 65000):
        return False
    if annonce.get("prix") and annonce["prix"] > criteres.get("budget_max", 42000):
        return False
    return True


def scraper(modele: dict = None) -> list:
    criteres = modele.get("criteres", {}) if modele else {}
    annonces = []
    try:
        params = _construire_params(criteres)
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            resp = client.get(API_URL, params=params, headers=HEADERS)
            resp.raise_for_status()
            data  = resp.json()
        items = data.get("data", data.get("listings", data.get("results", [])))
        for item in items:
            try:
                a = _normaliser_annonce(item)
                if _est_eligible(a, criteres):
                    annonces.append(a)
            except Exception as e:
                print(f"  ⚠️  Autohero normalisation : {e}")
        print(f"✅ Autohero — {len(annonces)} annonces éligibles")
    except httpx.HTTPStatusError as e:
        print(f"❌ Autohero — HTTP {e.response.status_code}")
    except Exception as e:
        print(f"❌ Autohero — {e}")
    return annonces
