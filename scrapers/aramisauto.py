# =============================================================
# scrapers/aramisauto.py — Scraper Aramisauto
# Aramisauto embarque du JSON dans ses pages (Next.js)
# Garantie 12 mois + 0 frais entretien 12 mois/15 000 km
# =============================================================

import httpx
import re
import json
from config import CRITERES

SOURCE_ID   = "aramisauto"
SOURCE_NOM  = "Aramisauto"
FIABILITE   = 10

SEARCH_URL  = "https://www.aramisauto.com/voitures/mercedes/classe-c-break/offres/hybride-rechargeable/"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Accept"         : "text/html,application/xhtml+xml",
    "Accept-Language": "fr-FR,fr;q=0.9",
}


def _extraire_json_nextjs(html: str) -> list:
    """Extrait les données JSON embarquées par Next.js."""
    # Pattern Next.js __NEXT_DATA__
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not match:
        return []
    try:
        data     = json.loads(match.group(1))
        props    = data.get("props", {}).get("pageProps", {})
        vehicles = (
            props.get("vehicles")
            or props.get("offers")
            or props.get("cars")
            or []
        )
        return vehicles if isinstance(vehicles, list) else []
    except Exception:
        return []


def _normaliser_annonce(item: dict) -> dict:
    """Normalise une annonce Aramisauto."""
    titre = (
        f"C300e Break reconditionné {item.get('year', '?')} · "
        f"{item.get('mileage', '?')} km"
    )

    equipements = [str(e).lower() for e in item.get("options", item.get("features", []))]
    toit = any("toit" in e or "panoram" in e or "sunroof" in e for e in equipements)

    url_slug = item.get("url", item.get("link", item.get("id", "")))
    url = url_slug if url_slug.startswith("http") else f"https://www.aramisauto.com{url_slug}"

    return {
        "source"              : SOURCE_NOM,
        "source_id"           : SOURCE_ID,
        "fiabilite_source"    : FIABILITE,
        "titre"               : titre,
        "vendeur"             : "Aramisauto (reconditionné)",
        "url"                 : url,
        "prix"                : item.get("price", item.get("currentPrice")),
        "annee"               : item.get("year", item.get("firstRegistrationYear")),
        "km"                  : item.get("mileage"),
        "puissance_ch"        : item.get("power"),
        "toit_ouvrant"        : toit if equipements else None,
        "garantie_mois"       : 12,   # systématique Aramisauto
        "premiere_main"       : None,
        "entretien_constructeur": None,
        "couleur"             : item.get("color"),
        "finition"            : item.get("trim", item.get("version")),
        "equipements_raw"     : equipements,
        "source_raw"          : item,
    }


def _est_eligible(annonce: dict) -> bool:
    if annonce.get("annee") and annonce["annee"] < CRITERES["annee_min"]:
        return False
    if annonce.get("km") and annonce["km"] > CRITERES["km_max"]:
        return False
    if annonce.get("prix") and annonce["prix"] > CRITERES["budget_max"]:
        return False
    return True


def scraper() -> list:
    annonces = []
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            resp = client.get(SEARCH_URL, headers=HEADERS)
            resp.raise_for_status()
            html = resp.text

        items = _extraire_json_nextjs(html)

        if not items:
            # Fallback : parser le HTML directement
            print("  ℹ️  Aramisauto — JSON Next.js non trouvé, parsing HTML fallback")
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # Chercher les cartes véhicules (structure Aramisauto)
            cards = soup.select("[data-testid='vehicle-card'], .vehicle-card, article.car-card")
            print(f"  ℹ️  Aramisauto — {len(cards)} cartes HTML trouvées")
            # Le parsing HTML complet est dans la v2 du scraper

        for item in items:
            try:
                annonce = _normaliser_annonce(item)
                if _est_eligible(annonce):
                    annonces.append(annonce)
            except Exception as e:
                print(f"  ⚠️  Aramisauto — Erreur normalisation : {e}")

        print(f"✅ Aramisauto — {len(annonces)} annonces éligibles trouvées")

    except httpx.HTTPStatusError as e:
        print(f"❌ Aramisauto — Erreur HTTP {e.response.status_code}")
    except Exception as e:
        print(f"❌ Aramisauto — Erreur : {e}")

    return annonces
