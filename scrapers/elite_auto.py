# =============================================================
# scrapers/elite_auto.py — Elite-Auto
# Garantie 12 mois — spécialiste véhicules premium
# =============================================================

import httpx
import re
import json
from bs4 import BeautifulSoup

SOURCE_ID  = "elite_auto"
SOURCE_NOM = "Elite-Auto"
FIABILITE  = 8

SEARCH_URL = "https://www.elite-auto.fr/occasion/hybride/marque-mercedes/modele-classe-c"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Accept"         : "text/html,application/xhtml+xml",
    "Accept-Language": "fr-FR,fr;q=0.9",
}


def _extraire_json_embedded(html: str) -> list:
    """Elite-Auto utilise parfois du JSON embarqué en script."""
    patterns = [
        r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
        r'"vehicles"\s*:\s*(\[.*?\])',
        r'"listings"\s*:\s*(\[.*?\])',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
    return []


def _parser_html(html: str) -> list:
    soup  = BeautifulSoup(html, "lxml")
    cards = soup.select(".vehicle-card, .car-card, article.offer, .listing-item")
    annonces = []

    for card in cards:
        try:
            texte = card.get_text(" ", strip=True).lower()

            # Filtrer sur C300e
            if "c 300" not in texte and "c300" not in texte and "300e" not in texte:
                continue

            prix_el = card.select_one(".price, .prix, [data-price]")
            prix    = None
            if prix_el:
                px = re.sub(r"[^\d]", "", prix_el.get_text())
                prix = int(px) if px else None

            km_el = card.select_one(".km, .mileage, [data-km]")
            km    = None
            if km_el:
                k = re.sub(r"[^\d]", "", km_el.get_text())
                km = int(k) if k else None

            annee = None
            m = re.search(r"(20\d{2})", texte)
            if m:
                annee = int(m.group(1))

            lien  = card.select_one("a[href]")
            url   = ""
            if lien:
                href = lien.get("href", "")
                url  = href if href.startswith("http") else f"https://www.elite-auto.fr{href}"

            toit = True if "toit ouvrant" in texte or "panoram" in texte else None

            annonces.append({
                "source"              : SOURCE_NOM,
                "source_id"           : SOURCE_ID,
                "fiabilite_source"    : FIABILITE,
                "titre"               : f"C300e Break Elite-Auto {annee or '?'} · {km or '?'} km",
                "vendeur"             : "Elite-Auto",
                "url"                 : url or SEARCH_URL,
                "prix"                : prix,
                "annee"               : annee,
                "km"                  : km,
                "toit_ouvrant"        : toit,
                "garantie_mois"       : 12,
                "premiere_main"       : None,
                "entretien_constructeur": None,
            })
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
    criteres = modele.get("criteres", {}) if modele else {}
    annonces = []
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            resp = client.get(SEARCH_URL, headers=HEADERS)
            resp.raise_for_status()
            html = resp.text

        # Essai JSON embarqué d'abord
        items = _extraire_json_embedded(html)
        if items:
            for item in items if isinstance(items, list) else []:
                try:
                    annee = item.get("year") or item.get("firstRegistrationYear")
                    km    = item.get("mileage")
                    prix  = item.get("price")
                    texte = str(item).lower()
                    toit  = True if "toit" in texte or "panoram" in texte else None
                    url   = item.get("url", SEARCH_URL)
                    if not url.startswith("http"):
                        url = f"https://www.elite-auto.fr{url}"
                    a = {
                        "source": SOURCE_NOM, "source_id": SOURCE_ID,
                        "fiabilite_source": FIABILITE,
                        "titre": f"C300e Break Elite-Auto {annee or '?'} · {km or '?'} km",
                        "vendeur": "Elite-Auto", "url": url,
                        "prix": prix, "annee": annee, "km": km,
                        "toit_ouvrant": toit, "garantie_mois": 12,
                        "premiere_main": None, "entretien_constructeur": None,
                    }
                    if _est_eligible(a, criteres):
                        annonces.append(a)
                except Exception:
                    continue
        else:
            # Fallback HTML
            annonces = [a for a in _parser_html(html) if _est_eligible(a, criteres)]

        print(f"✅ Elite-Auto — {len(annonces)} annonces éligibles")

    except httpx.HTTPStatusError as e:
        print(f"❌ Elite-Auto — HTTP {e.response.status_code}")
    except Exception as e:
        print(f"❌ Elite-Auto — {e}")

    return annonces
