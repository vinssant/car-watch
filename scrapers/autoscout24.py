# =============================================================
# scrapers/autoscout24.py — Scraper Autoscout24 v2
# Parsing HTML direct + fallback JSON
# =============================================================

import httpx
import re
import json
from bs4 import BeautifulSoup

SOURCE_ID  = "autoscout24"
SOURCE_NOM = "Autoscout24"
FIABILITE  = 6

SEARCH_URL = "https://www.autoscout24.fr/lst/mercedes-benz/c-300-e/bt_estate"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept"         : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}


def _extraire_via_json(html: str) -> list:
    """Tente d'extraire via __NEXT_DATA__."""
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not match:
        return []
    try:
        data  = json.loads(match.group(1))
        # Chercher listings à plusieurs niveaux
        def find_listings(obj, depth=0):
            if depth > 6 or not isinstance(obj, (dict, list)):
                return []
            if isinstance(obj, list) and len(obj) > 0:
                first = obj[0]
                if isinstance(first, dict) and any(k in first for k in ["id", "price", "mileage", "firstRegistration"]):
                    return obj
            if isinstance(obj, dict):
                for key in ["listings", "vehicles", "results", "ads", "data", "items"]:
                    if key in obj:
                        result = find_listings(obj[key], depth + 1)
                        if result:
                            return result
                for v in obj.values():
                    result = find_listings(v, depth + 1)
                    if result:
                        return result
            return []
        return find_listings(data)
    except Exception:
        return []


def _normaliser_json(item: dict) -> dict:
    annee_raw = item.get("firstRegistration", "") or ""
    annee     = int(str(annee_raw)[:4]) if str(annee_raw)[:4].isdigit() else None
    km        = item.get("mileage")
    
    # Prix — plusieurs formats possibles
    prix = None
    p    = item.get("price") or item.get("prices", {})
    if isinstance(p, (int, float)):
        prix = int(p)
    elif isinstance(p, dict):
        prix = p.get("consumer", {}).get("priceRaw") or p.get("public", {}).get("priceRaw") or p.get("value")

    titre = item.get("title") or item.get("name") or f"C300e Break {annee or '?'} · {km or '?'} km"

    seller  = item.get("seller", {}) or {}
    loc     = seller.get("location", {}) or {}
    ville   = loc.get("city", "") if isinstance(loc, dict) else ""
    cp      = str(loc.get("zip", ""))[:2] if isinstance(loc, dict) else ""
    vendeur = f"{seller.get('name', 'Pro AS24')} ({ville} {cp})".strip(" ()")

    ad_id = item.get("id", item.get("vehicleId", ""))
    url   = f"https://www.autoscout24.fr/annonces/{ad_id}" if ad_id else SEARCH_URL

    equips = [str(e).lower() for e in (item.get("features") or item.get("equipmentList") or [])]
    desc   = str(item.get("description", "")).lower()
    toit   = True if any("toit" in e or "panoram" in e for e in equips) or "toit ouvrant" in desc else None

    garantie = None
    m = re.search(r"garantie\s+(\d+)\s*mois", desc)
    if m:
        garantie = int(m.group(1))

    return {
        "source": SOURCE_NOM, "source_id": SOURCE_ID,
        "fiabilite_source": FIABILITE,
        "titre": titre, "vendeur": vendeur, "url": url,
        "prix": prix, "annee": annee, "km": km,
        "toit_ouvrant": toit, "garantie_mois": garantie,
        "premiere_main": item.get("previousOwners") == 1,
        "entretien_constructeur": None,
    }


def _parser_html(html: str, criteres: dict) -> list:
    """Fallback : parsing HTML direct des cards Autoscout24."""
    soup     = BeautifulSoup(html, "lxml")
    annonces = []

    # Autoscout24 utilise des articles avec data-testid ou class spécifique
    cards = soup.select("article[data-testid], article.cl-list-element, [data-item-name='listing-item']")
    
    if not cards:
        # Essai avec les liens d'annonces directement
        cards = soup.select("a[href*='/annonces/']")

    for card in cards:
        try:
            texte = card.get_text(" ", strip=True)

            # Prix
            prix = None
            prix_match = re.search(r"([\d\s]{2,})\s*€", texte)
            if prix_match:
                px = re.sub(r"\s", "", prix_match.group(1))
                if px.isdigit() and 10000 < int(px) < 200000:
                    prix = int(px)

            # Kilométrage
            km = None
            km_match = re.search(r"([\d\s]+)\s*km", texte)
            if km_match:
                k = re.sub(r"\s", "", km_match.group(1))
                if k.isdigit() and 100 < int(k) < 300000:
                    km = int(k)

            # Année
            annee = None
            annee_match = re.search(r"\b(202[0-9])\b", texte)
            if annee_match:
                annee = int(annee_match.group(1))

            # URL
            lien  = card.select_one("a[href*='/annonces/']") or card if card.name == "a" else None
            url   = ""
            if lien and lien.get("href"):
                href = lien["href"]
                url  = href if href.startswith("http") else f"https://www.autoscout24.fr{href}"

            if not url:
                continue

            toit = True if "toit ouvrant" in texte.lower() or "panoram" in texte.lower() else None

            a = {
                "source": SOURCE_NOM, "source_id": SOURCE_ID,
                "fiabilite_source": FIABILITE,
                "titre": f"C300e Break {annee or '?'} · {km or '?'} km",
                "vendeur": "Pro Autoscout24",
                "url": url,
                "prix": prix, "annee": annee, "km": km,
                "toit_ouvrant": toit, "garantie_mois": None,
                "premiere_main": None, "entretien_constructeur": None,
            }

            if _est_eligible(a, criteres):
                annonces.append(a)

        except Exception:
            continue

    return annonces


def _est_eligible(annonce: dict, criteres: dict) -> bool:
    if annonce.get("annee") and annonce["annee"] < criteres.get("annee_min", 2023):
        return False
    if annonce.get("km") and annonce["km"] > criteres.get("km_max", 65000):
        return False
    if annonce.get("prix") and annonce["prix"] > criteres.get("budget_max", 42000):
        return False
    return True


def scraper(modele: dict = None) -> list:
    criteres  = modele.get("criteres", {}) if modele else {}
    annonces  = []
    annee_min = criteres.get("annee_min", 2023)
    budget    = criteres.get("budget_max", 42000)
    km_max    = criteres.get("km_max", 65000)

    url = f"{SEARCH_URL}?fregfrom={annee_min}&priceto={budget}&kmto={km_max}&ustate=U&cy=F"

    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
            resp = client.get(url, headers=HEADERS)
            resp.raise_for_status()
            html = resp.text

        # Tentative 1 : JSON embarqué
        items = _extraire_via_json(html)
        if items:
            for item in items:
                try:
                    a = _normaliser_json(item)
                    if _est_eligible(a, criteres):
                        annonces.append(a)
                except Exception:
                    continue
            print(f"✅ Autoscout24 (JSON) — {len(annonces)} annonces éligibles")
        else:
            # Tentative 2 : HTML direct
            annonces = _parser_html(html, criteres)
            print(f"✅ Autoscout24 (HTML) — {len(annonces)} annonces éligibles")

    except httpx.HTTPStatusError as e:
        print(f"❌ Autoscout24 — HTTP {e.response.status_code}")
    except Exception as e:
        print(f"❌ Autoscout24 — {e}")

    return annonces
