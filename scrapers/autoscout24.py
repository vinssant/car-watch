# =============================================================
# scrapers/autoscout24.py — Scraper Autoscout24 v3
# Utilise l'API interne d'Autoscout24 via les paramètres corrects
# =============================================================

import httpx
import re
import json

SOURCE_ID  = "autoscout24"
SOURCE_NOM = "Autoscout24"
FIABILITE  = 6

# API JSON interne Autoscout24 (mobile/app endpoint)
API_URLS = [
    "https://www.autoscout24.fr/api/offers",
    "https://www.autoscout24.fr/api/v1/offers",
    "https://listing.autoscout24.com/offers",
]

SEARCH_URL_BASE = "https://www.autoscout24.fr/lst/mercedes-benz/c-300-e"

HEADERS_JSON = {
    "User-Agent"      : "AutoScout24/9.12.0 (iPhone; iOS 16.0; Scale/3.00)",
    "Accept"          : "application/json",
    "Accept-Language" : "fr-FR",
    "X-AS24-Client"   : "as24-mobile-ios",
}

HEADERS_HTML = {
    "User-Agent"      : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0",
    "Accept"          : "text/html,application/xhtml+xml",
    "Accept-Language" : "fr-FR,fr;q=0.9",
}


def _params_recherche(criteres: dict, page: int = 1) -> dict:
    return {
        "make"    : "Mercedes",
        "model"   : "C-Klasse",
        "body"    : "Combi",  # Break en allemand pour AS24
        "fuel"    : "Hybride",
        "year_from": criteres.get("annee_min", 2023),
        "price_to": criteres.get("budget_max", 42000),
        "km_to"   : criteres.get("km_max", 65000),
        "country" : "F",
        "page"    : page,
        "size"    : 20,
        "sort"    : "price",
        "desc"    : 0,
    }


def _params_url(criteres: dict) -> dict:
    """Paramètres pour l'URL de recherche standard."""
    return {
        "fregfrom" : criteres.get("annee_min", 2023),
        "priceto"  : criteres.get("budget_max", 42000),
        "kmto"     : criteres.get("km_max", 65000),
        "ustate"   : "U",
        "cy"       : "F",
        "atype"    : "C",
        "size"     : 20,
        "page"     : 1,
    }


def _extraire_json_page(html: str) -> list:
    """Cherche agressivement le JSON dans la page."""
    # Pattern 1 : __NEXT_DATA__
    m = re.search(r'"listings"\s*:\s*(\[[\s\S]*?\])\s*,\s*"(?:totalCount|pagination|meta)"', html)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # Pattern 2 : tableau JSON avec id + price
    for pattern in [
        r'\{"id":"[^"]+","price":\{',
        r'\{"vehicleId":"[^"]+","prices":\{',
    ]:
        pos = [m.start() for m in re.finditer(pattern, html)]
        if pos:
            items = []
            for p in pos[:20]:
                # Extraire l'objet JSON à cette position
                depth, end = 0, p
                for i, c in enumerate(html[p:p+2000]):
                    if c == '{':
                        depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0:
                            end = p + i + 1
                            break
                try:
                    items.append(json.loads(html[p:end]))
                except Exception:
                    pass
            if items:
                return items

    return []


def _normaliser(item: dict) ->object:
    """Normalise un item JSON Autoscout24 — retourne None si données insuffisantes."""

    # Prix
    prix = None
    for p_key in ["price", "prices"]:
        p = item.get(p_key)
        if isinstance(p, (int, float)) and p > 0:
            prix = int(p)
            break
        elif isinstance(p, dict):
            for sub in ["consumer", "public", "retail"]:
                raw = p.get(sub, {}).get("priceRaw") or p.get(sub, {}).get("value") or p.get(sub)
                if isinstance(raw, (int, float)) and raw > 0:
                    prix = int(raw)
                    break
            if prix:
                break

    # Km
    km = None
    for k_key in ["mileage", "km", "kilometres"]:
        k = item.get(k_key)
        if isinstance(k, (int, float)) and k > 0:
            km = int(k)
            break
        elif isinstance(k, dict):
            km = k.get("value")
            if km:
                km = int(km)
                break

    # Année
    annee = None
    for a_key in ["firstRegistration", "registrationYear", "year", "modelYear"]:
        a = item.get(a_key)
        if a:
            a_str = str(a)[:4]
            if a_str.isdigit() and 2018 <= int(a_str) <= 2026:
                annee = int(a_str)
                break

    # Rejeter si données insuffisantes (prix ET km manquants = annonce inutilisable)
    if prix is None and km is None:
        return None

    # ID et URL
    ad_id = item.get("id") or item.get("vehicleId") or item.get("listingId", "")
    url   = item.get("url", "")
    if not url and ad_id:
        url = f"https://www.autoscout24.fr/annonces/{ad_id}"
    if not url:
        return None

    # Vendeur
    seller  = item.get("seller", item.get("dealer", {})) or {}
    loc     = seller.get("location", {}) if isinstance(seller, dict) else {}
    ville   = loc.get("city", "") if isinstance(loc, dict) else ""
    cp_raw  = str(loc.get("zip", ""))[:2] if isinstance(loc, dict) else ""
    vendeur = f"{seller.get('name', 'Pro AS24') if isinstance(seller, dict) else 'Pro AS24'}"
    if ville:
        vendeur += f" ({ville} {cp_raw})".rstrip()

    # Titre
    titre = item.get("title") or item.get("name") or f"C300e Break {annee or '?'} · {km or '?'} km"

    # Équipements
    equips = [str(e).lower() for e in (item.get("features") or item.get("equipmentList") or [])]
    desc   = str(item.get("description", "")).lower()
    toit   = True if any("toit" in e or "panoram" in e for e in equips) or "toit ouvrant" in desc else None

    garantie = None
    m2 = re.search(r"garantie\s+(\d+)\s*mois", desc)
    if m2:
        garantie = int(m2.group(1))

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
        "premiere_main"       : item.get("previousOwners") == 1,
        "entretien_constructeur": None,
    }


def _est_eligible(a: dict, criteres: dict) -> bool:
    if a.get("annee") and a["annee"] < criteres.get("annee_min", 2023):
        return False
    if a.get("km") and a["km"] > criteres.get("km_max", 65000):
        return False
    if a.get("prix") and a["prix"] > criteres.get("budget_max", 42000):
        return False
    return True


def scraper(modele: dict = None) -> list:
    criteres = modele.get("criteres", {}) if modele else {}
    annonces = []

    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
            # Essai 1 : URL de recherche standard avec JSON embarqué
            url = SEARCH_URL_BASE
            params = _params_url(criteres)
            resp = client.get(url, params=params, headers=HEADERS_HTML)

            if resp.status_code == 200:
                items = _extraire_json_page(resp.text)
                for item in items:
                    a = _normaliser(item)
                    if a and _est_eligible(a, criteres):
                        annonces.append(a)

            # Essai 2 : variante avec /bt_estate
            if not annonces:
                url2 = SEARCH_URL_BASE + "/bt_estate"
                resp2 = client.get(url2, params=params, headers=HEADERS_HTML)
                if resp2.status_code == 200:
                    items2 = _extraire_json_page(resp2.text)
                    for item in items2:
                        a = _normaliser(item)
                        if a and _est_eligible(a, criteres):
                            annonces.append(a)

    except Exception as e:
        print(f"❌ Autoscout24 — {e}")

    # Dédupliquer par URL
    seen  = set()
    dedup = []
    for a in annonces:
        if a["url"] not in seen:
            seen.add(a["url"])
            dedup.append(a)

    print(f"✅ Autoscout24 — {len(dedup)} annonces éligibles")
    return dedup
