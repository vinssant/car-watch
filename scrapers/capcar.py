# =============================================================
# scrapers/capcar.py — CapCar
# Inspection indépendante — garantie 6 mois + extension
# =============================================================

import httpx
import re
import json

SOURCE_ID  = "capcar"
SOURCE_NOM = "CapCar"
FIABILITE  = 7

API_URL = "https://www.capcar.fr/api/cars/search"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Accept"         : "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer"        : "https://www.capcar.fr/",
}


def _construire_params(criteres: dict) -> dict:
    return {
        "make"        : "mercedes-benz",
        "model"       : "classe-c",
        "body"        : "break",
        "fuel"        : "hybride-rechargeable",
        "yearMin"     : criteres.get("annee_min", 2023),
        "priceMax"    : criteres.get("budget_max", 42000),
        "mileageMax"  : criteres.get("km_max", 65000),
        "page"        : 1,
        "limit"       : 30,
        "sort"        : "price_asc",
    }


def _normaliser_annonce(item: dict) -> dict:
    annee  = item.get("year") or item.get("registrationYear")
    km     = item.get("mileage")
    prix   = item.get("price") or item.get("sellingPrice")
    titre  = item.get("title", f"C300e Break CapCar {annee or '?'} · {km or '?'} km")

    texte  = str(item).lower()
    toit   = True if "toit ouvrant" in texte or "panoram" in texte else None

    slug   = item.get("slug", item.get("id", ""))
    url    = f"https://www.capcar.fr/voiture/{slug}" if slug else "https://www.capcar.fr/"

    ville  = item.get("city", item.get("location", {}).get("city", "")) if isinstance(item.get("location"), dict) else item.get("city", "")
    vendeur = f"CapCar — {ville}".strip(" —")

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
        "garantie_mois"       : 6,   # CapCar standard
        "premiere_main"       : None,
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

        items = data.get("cars", data.get("results", data.get("data", [])))

        for item in items:
            try:
                a = _normaliser_annonce(item)
                if _est_eligible(a, criteres):
                    annonces.append(a)
            except Exception as e:
                print(f"  ⚠️  CapCar normalisation : {e}")

        print(f"✅ CapCar — {len(annonces)} annonces éligibles")

    except httpx.HTTPStatusError as e:
        print(f"❌ CapCar — HTTP {e.response.status_code}")
    except Exception as e:
        print(f"❌ CapCar — {e}")

    return annonces
