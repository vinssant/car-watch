# =============================================================
# scrapers/aramisauto.py — Scraper Aramisauto
# Garantie 12 mois + 0 frais entretien 12 mois/15 000 km
# =============================================================

import httpx, re, json

SOURCE_ID  = "aramisauto"
SOURCE_NOM = "Aramisauto"
FIABILITE  = 10

SEARCH_URL = "https://www.aramisauto.com/voitures/mercedes/classe-c-break/offres/hybride-rechargeable/"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept"         : "text/html,application/xhtml+xml",
    "Accept-Language": "fr-FR,fr;q=0.9",
}


def _extraire_json_nextjs(html: str) -> list:
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not match:
        return []
    try:
        data  = json.loads(match.group(1))
        props = data.get("props", {}).get("pageProps", {})
        v     = props.get("vehicles") or props.get("offers") or props.get("cars") or []
        return v if isinstance(v, list) else []
    except Exception:
        return []


def _normaliser_annonce(item: dict) -> dict:
    annee  = item.get("year", item.get("firstRegistrationYear"))
    km     = item.get("mileage")
    titre  = f"C300e Break reconditionné {annee or '?'} · {km or '?'} km"
    equips = [str(e).lower() for e in item.get("options", item.get("features", []))]
    toit   = any("toit" in e or "panoram" in e for e in equips) if equips else None
    url    = item.get("url", item.get("link", ""))
    if url and not url.startswith("http"):
        url = f"https://www.aramisauto.com{url}"

    return {
        "source"              : SOURCE_NOM,
        "source_id"           : SOURCE_ID,
        "fiabilite_source"    : FIABILITE,
        "titre"               : titre,
        "vendeur"             : "Aramisauto (reconditionné)",
        "url"                 : url or SEARCH_URL,
        "prix"                : item.get("price", item.get("currentPrice")),
        "annee"               : annee,
        "km"                  : km,
        "toit_ouvrant"        : toit,
        "garantie_mois"       : 12,
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
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            resp = client.get(SEARCH_URL, headers=HEADERS)
            resp.raise_for_status()
            items = _extraire_json_nextjs(resp.text)
        for item in items:
            try:
                a = _normaliser_annonce(item)
                if _est_eligible(a, criteres):
                    annonces.append(a)
            except Exception as e:
                print(f"  ⚠️  Aramisauto normalisation : {e}")
        print(f"✅ Aramisauto — {len(annonces)} annonces éligibles")
    except Exception as e:
        print(f"❌ Aramisauto — {e}")
    return annonces
