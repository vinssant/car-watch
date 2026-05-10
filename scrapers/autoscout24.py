# =============================================================
# scrapers/autoscout24.py — Scraper Autoscout24
# Couverture France + Belgique
# URL corrigée pour C300e break
# =============================================================

import httpx
import re
import json
from bs4 import BeautifulSoup

SOURCE_ID  = "autoscout24"
SOURCE_NOM = "Autoscout24"
FIABILITE  = 6

# URLs correctes pour Mercedes C300e break
SEARCH_URLS = [
    "https://www.autoscout24.fr/lst/mercedes-benz/c-300/ve_e/bt_estate",
    "https://www.autoscout24.fr/lst/mercedes-benz/c-300-e/bt_estate",
]

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept"         : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection"     : "keep-alive",
}


def _extraire_json_as24(html: str) -> list:
    """Extrait les données JSON embarquées par Autoscout24 (Next.js)."""
    # Pattern principal __NEXT_DATA__
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if match:
        try:
            data     = json.loads(match.group(1))
            props    = data.get("props", {}).get("pageProps", {})
            listings = (
                props.get("listings")
                or props.get("initialData", {}).get("listings")
                or props.get("data", {}).get("listings")
                or []
            )
            return listings if isinstance(listings, list) else []
        except Exception:
            pass

    # Pattern alternatif : window.__NUXT__
    match2 = re.search(r'window\.__NUXT__\s*=\s*({.*?});', html, re.DOTALL)
    if match2:
        try:
            data = json.loads(match2.group(1))
            return data.get("listings", [])
        except Exception:
            pass

    return []


def _normaliser_annonce(item: dict) -> dict:
    """Normalise une annonce Autoscout24."""
    # Données de base
    annee_str = str(item.get("firstRegistration", ""))[:4]
    annee     = int(annee_str) if annee_str.isdigit() else None
    km        = item.get("mileage")
    titre_raw = item.get("title", item.get("name", ""))
    titre     = titre_raw or f"C300e Break {annee or '?'} · {km or '?'} km"

    # Prix
    prix_data = item.get("prices", {})
    if isinstance(prix_data, dict):
        prix = prix_data.get("public", {}).get("priceRaw") or prix_data.get("consumer", {}).get("priceRaw")
    else:
        prix = item.get("price")

    # Vendeur
    seller  = item.get("seller", {})
    ville   = seller.get("location", {}).get("city", "") if isinstance(seller.get("location"), dict) else ""
    cp      = str(seller.get("location", {}).get("zip", ""))[:2] if isinstance(seller.get("location"), dict) else ""
    vendeur = f"{seller.get('name', 'Pro AS24')} ({ville} {cp})".strip("()")

    # URL
    ad_id = item.get("id", "")
    url   = f"https://www.autoscout24.fr/annonces/{ad_id}" if ad_id else SEARCH_URLS[0]

    # Équipements
    equips = [str(e).lower() for e in item.get("features", item.get("equipmentList", []))]
    toit   = True if any("toit" in e or "panoram" in e or "sunroof" in e or "glassdach" in e for e in equips) else None

    # Garantie dans description
    desc     = str(item.get("description", "")).lower()
    garantie = None
    m = re.search(r"garantie\s+(\d+)\s*mois", desc)
    if m:
        garantie = int(m.group(1))

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
        "premiere_main"       : item.get("previousOwners") == 1 or item.get("ownerCount") == 1,
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

    # Paramètres de filtre en URL
    annee_min = criteres.get("annee_min", 2023)
    budget    = criteres.get("budget_max", 42000)
    km_max    = criteres.get("km_max", 65000)

    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
            for base_url in SEARCH_URLS:
                url = f"{base_url}?fregfrom={annee_min}&priceto={budget}&kmto={km_max}&ustate=U&cy=F"
                try:
                    resp = client.get(url, headers=HEADERS)
                    if resp.status_code != 200:
                        continue

                    items = _extraire_json_as24(resp.text)
                    if items:
                        for item in items:
                            try:
                                a = _normaliser_annonce(item)
                                if _est_eligible(a, criteres):
                                    annonces.append(a)
                            except Exception:
                                continue
                        break  # On a des résultats, pas besoin d'essayer l'autre URL

                except Exception:
                    continue

        print(f"✅ Autoscout24 — {len(annonces)} annonces éligibles")

    except Exception as e:
        print(f"❌ Autoscout24 — {e}")

    return annonces
