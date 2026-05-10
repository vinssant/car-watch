# =============================================================
# scrapers/lacentrale.py — La Centrale
# Agrégateur — garantie variable selon vendeur
# =============================================================

import httpx
import re
import json

SOURCE_ID  = "lacentrale"
SOURCE_NOM = "La Centrale"
FIABILITE  = 6

# API La Centrale (JSON)
API_URL = "https://www.lacentrale.fr/api/search/vehicle"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Accept"         : "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer"        : "https://www.lacentrale.fr/",
}


def _construire_params(criteres: dict) -> dict:
    return {
        "makesModelsCommercialNames": "MERCEDES BENZ:CLASSE C",
        "energies"                  : "HYBRIDE RECHARGEABLE",
        "bodyTypes"                 : "BREAK",
        "yearMin"                   : criteres.get("annee_min", 2023),
        "priceMax"                  : criteres.get("budget_max", 42000),
        "mileageMax"                : criteres.get("km_max", 65000),
        "page"                      : 1,
        "pageSize"                  : 30,
        "sortBy"                    : "PRICE_ASC",
        "isDealer"                  : True,
    }


def _normaliser_annonce(item: dict) -> dict:
    annee  = item.get("year") or item.get("registrationYear")
    km     = item.get("mileage") or item.get("km")
    prix   = item.get("price") or item.get("sellingPrice")
    titre  = item.get("title", f"C300e Break {annee or '?'} · {km or '?'} km")

    seller = item.get("seller", item.get("dealer", {}))
    ville  = seller.get("city", seller.get("location", "")) if isinstance(seller, dict) else ""
    vendeur = f"{seller.get('name', 'Pro') if isinstance(seller, dict) else 'Pro'} ({ville})".strip("()")

    options = [str(o).lower() for o in item.get("options", item.get("features", []))]
    desc    = str(item.get("description", "")).lower()
    toit    = True if any("toit" in o or "panoram" in o for o in options) or "toit ouvrant" in desc else None

    garantie = None
    m = re.search(r"garantie\s+(\d+)\s*mois", desc)
    if m:
        garantie = int(m.group(1))

    ad_id = item.get("id", item.get("adId", ""))
    url   = f"https://www.lacentrale.fr/auto-occasion-annonce-{ad_id}.html" if ad_id else "https://www.lacentrale.fr/"

    return {
        "source"              : SOURCE_NOM,
        "source_id"           : SOURCE_ID,
        "fiabilite_source"    : FIABILITE,
        "titre"               : titre,
        "vendeur"             : vendeur,
        "url"                 : url,
        "prix"                : prix,
        "annee"               : annee,
        "km"                  : km,
        "toit_ouvrant"        : toit,
        "garantie_mois"       : garantie,
        "premiere_main"       : item.get("ownerCount") == 1,
        "entretien_constructeur": None,
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

        items = data.get("ads", data.get("vehicles", data.get("results", [])))

        for item in items:
            try:
                a = _normaliser_annonce(item)
                if _est_eligible(a, criteres):
                    annonces.append(a)
            except Exception as e:
                print(f"  ⚠️  La Centrale normalisation : {e}")

        print(f"✅ La Centrale — {len(annonces)} annonces éligibles")

    except httpx.HTTPStatusError as e:
        print(f"❌ La Centrale — HTTP {e.response.status_code}")
    except Exception as e:
        print(f"❌ La Centrale — {e}")

    return annonces
