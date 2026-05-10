# =============================================================
# scrapers/autouncle.py — AutoUncle
# Agrégateur avec cote marché — données structurées JSON
# Source très fiable pour détecter les annonces sous la cote
# =============================================================

import httpx
import re
import json

SOURCE_ID  = "autouncle"
SOURCE_NOM = "AutoUncle"
FIABILITE  = 6

# API AutoUncle (JSON accessible)
API_URL = "https://www.autouncle.fr/fr/search/cars.json"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0",
    "Accept"         : "application/json, text/javascript, */*",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer"        : "https://www.autouncle.fr/fr/voitures-occasion/Mercedes/C300e",
    "X-Requested-With": "XMLHttpRequest",
}


def _construire_params(criteres: dict) -> dict:
    return {
        "make"          : "Mercedes",
        "model"         : "C300e",
        "body_type"     : "estate",
        "fuel_type"     : "hybrid",
        "year_min"      : criteres.get("annee_min", 2023),
        "price_max"     : criteres.get("budget_max", 42000),
        "mileage_max"   : criteres.get("km_max", 65000),
        "country"       : "FR",
        "page"          : 1,
        "per_page"      : 30,
        "sort"          : "price_asc",
        "seller_type"   : "dealer",
    }


def _normaliser_annonce(item: dict) -> dict:
    annee  = item.get("year") or item.get("registration_year")
    km     = item.get("mileage") or item.get("km")
    prix   = item.get("price") or item.get("asking_price")
    titre  = item.get("title") or f"C300e Break {annee or '?'} · {km or '?'} km"

    seller = item.get("seller", item.get("dealer", {}))
    ville  = seller.get("city", seller.get("location", "")) if isinstance(seller, dict) else ""
    vendeur = f"{seller.get('name', 'Pro') if isinstance(seller, dict) else 'Pro'} ({ville})".strip("()")

    url    = item.get("url", item.get("link", ""))
    if url and not url.startswith("http"):
        url = f"https://www.autouncle.fr{url}"

    texte  = str(item).lower()
    toit   = True if "toit ouvrant" in texte or "panoram" in texte or "sunroof" in texte else None

    # Cote AutoUncle
    cote        = item.get("market_price") or item.get("fair_price")
    sous_la_cote = None
    if cote and prix:
        diff = cote - prix
        if diff > 0:
            sous_la_cote = round(diff)

    return {
        "source"              : SOURCE_NOM,
        "source_id"           : SOURCE_ID,
        "fiabilite_source"    : FIABILITE,
        "titre"               : titre,
        "vendeur"             : vendeur,
        "url"                 : url or "https://www.autouncle.fr/fr/voitures-occasion/Mercedes/C300e",
        "prix"                : prix,
        "annee"               : annee,
        "km"                  : km,
        "toit_ouvrant"        : toit,
        "garantie_mois"       : None,
        "premiere_main"       : item.get("owners") == 1,
        "entretien_constructeur": None,
        "cote_marche"         : cote,
        "sous_la_cote"        : sous_la_cote,
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
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            resp = client.get(API_URL, params=params, headers=HEADERS)
            resp.raise_for_status()
            data  = resp.json()

        items = data.get("cars", data.get("listings", data.get("results", [])))

        for item in items:
            try:
                a = _normaliser_annonce(item)
                if _est_eligible(a, criteres):
                    annonces.append(a)
            except Exception as e:
                print(f"  ⚠️  AutoUncle normalisation : {e}")

        print(f"✅ AutoUncle — {len(annonces)} annonces éligibles")

    except httpx.HTTPStatusError as e:
        print(f"❌ AutoUncle — HTTP {e.response.status_code}")
    except Exception as e:
        print(f"❌ AutoUncle — {e}")

    return annonces
