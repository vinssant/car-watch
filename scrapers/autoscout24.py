# =============================================================
# scrapers/autoscout24.py — Scraper Autoscout24
# Couverture France + Belgique
# =============================================================

import httpx, re

SOURCE_ID  = "autoscout24"
SOURCE_NOM = "Autoscout24"
FIABILITE  = 6

API_BASE = "https://www.autoscout24.fr/lst/mercedes-benz/c-300"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept"         : "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer"        : "https://www.autoscout24.fr/",
}


def _construire_params(criteres: dict, page: int = 1) -> dict:
    return {
        "atype"   : "C",
        "body"    : "8",
        "fuel"    : "H",
        "fregfrom": criteres.get("annee_min", 2023),
        "priceto" : criteres.get("budget_max", 42000),
        "kmto"    : criteres.get("km_max", 65000),
        "cy"      : "F",
        "ustate"  : "U",
        "size"    : 20,
        "page"    : page,
        "sort"    : "price",
        "desc"    : 0,
    }


def _normaliser_annonce(item: dict) -> dict:
    annee_str = item.get("firstRegistration", "")[:4]
    annee     = int(annee_str) if annee_str.isdigit() else None
    km        = item.get("mileage")
    titre     = f"C300e Break {annee or '?'} · {km or '?'} km"

    seller    = item.get("seller", {})
    loc       = seller.get("location", {})
    ville     = loc.get("city", "")
    cp        = str(loc.get("zip", ""))[:2]
    vendeur   = f"{seller.get('name', 'Pro')} ({ville} {cp})".strip()

    equips    = [str(e).lower() for e in item.get("highlights", [])]
    toit      = any("panoram" in e or "toit" in e or "sunroof" in e for e in equips) if equips else None

    prix_data = item.get("prices", {}).get("public", {})
    prix      = prix_data.get("priceRaw") or item.get("price")

    garantie  = None
    desc      = str(item.get("description", "")).lower()
    m         = re.search(r"garantie\s+(\d+)\s*mois", desc)
    if m:
        garantie = int(m.group(1))

    return {
        "source"              : SOURCE_NOM,
        "source_id"           : SOURCE_ID,
        "fiabilite_source"    : FIABILITE,
        "titre"               : titre,
        "vendeur"             : vendeur,
        "url"                 : f"https://www.autoscout24.fr/annonces/mercedes-benz-classe-c-{item.get('id','')}",
        "prix"                : prix,
        "annee"               : annee,
        "km"                  : km,
        "toit_ouvrant"        : toit,
        "garantie_mois"       : garantie,
        "premiere_main"       : item.get("previousOwners") == 1,
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
            for page in range(1, 4):
                resp = client.get(API_BASE, params=_construire_params(criteres, page), headers=HEADERS)
                resp.raise_for_status()
                try:
                    data  = resp.json()
                    items = data.get("listings", data.get("results", []))
                except Exception:
                    break
                if not items:
                    break
                for item in items:
                    try:
                        a = _normaliser_annonce(item)
                        if _est_eligible(a, criteres):
                            annonces.append(a)
                    except Exception as e:
                        print(f"  ⚠️  Autoscout24 normalisation : {e}")
                total = data.get("totalCount", 0)
                if page * 20 >= total:
                    break
        print(f"✅ Autoscout24 — {len(annonces)} annonces éligibles")
    except Exception as e:
        print(f"❌ Autoscout24 — {e}")
    return annonces
