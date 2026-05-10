# =============================================================
# scrapers/mercedes_certified.py — Mercedes-Benz Certified
# Réseau officiel — Garantie 12-24 mois constructeur
# =============================================================

import httpx
import re
import json
from bs4 import BeautifulSoup

SOURCE_ID  = "mercedes_certified"
SOURCE_NOM = "Mercedes-Benz Certified"
FIABILITE  = 10

# API Mercedes occasion (reverse-engineered)
API_URL = "https://shop.mercedes-benz.com/used-cars/api/v1/vehicles"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Accept"         : "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer"        : "https://www.mercedes-benz.fr/",
}


def _construire_params(criteres: dict) -> dict:
    return {
        "country"      : "fr",
        "language"     : "fr",
        "make"         : "mercedes-benz",
        "model"        : "c-class",
        "bodyStyle"    : "estate",
        "fuelType"     : "PLUGIN_HYBRID_ELECTRIC",
        "yearFrom"     : criteres.get("annee_min", 2023),
        "priceMax"     : criteres.get("budget_max", 42000),
        "mileageMax"   : criteres.get("km_max", 65000),
        "pageSize"     : 30,
        "page"         : 0,
        "sortBy"       : "price",
        "sortOrder"    : "asc",
    }


def _normaliser_annonce(item: dict) -> dict:
    annee  = item.get("firstRegistrationYear") or item.get("modelYear")
    km     = item.get("mileage", {}).get("value") if isinstance(item.get("mileage"), dict) else item.get("mileage")
    prix   = item.get("price", {}).get("value") if isinstance(item.get("price"), dict) else item.get("price")
    titre  = f"C300e Break Certified {annee or '?'} · {km or '?'} km"

    equips = [str(e).lower() for e in item.get("equipmentList", item.get("features", []))]
    toit   = any("toit" in e or "panoram" in e or "sunroof" in e for e in equips) if equips else None

    dealer = item.get("dealer", {})
    ville  = dealer.get("city", "") if isinstance(dealer, dict) else ""
    vendeur = f"MB Certified — {ville}".strip(" —")

    ad_id  = item.get("id", item.get("vehicleId", ""))
    url    = f"https://shop.mercedes-benz.com/used-cars/fr/fr/details/{ad_id}" if ad_id else "https://www.mercedes-benz.fr/passengercars/buy/used-cars.html"

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
        "garantie_mois"       : 12,  # minimum MB Certified
        "premiere_main"       : None,
        "entretien_constructeur": True,
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

        items = data.get("vehicles", data.get("results", data.get("data", [])))

        for item in items:
            try:
                a = _normaliser_annonce(item)
                if _est_eligible(a, criteres):
                    annonces.append(a)
            except Exception as e:
                print(f"  ⚠️  MB Certified normalisation : {e}")

        print(f"✅ MB Certified — {len(annonces)} annonces éligibles")

    except httpx.HTTPStatusError as e:
        print(f"❌ MB Certified — HTTP {e.response.status_code}")
    except Exception as e:
        print(f"❌ MB Certified — {e}")

    return annonces
