# =============================================================
# scrapers/autoscout24.py — Scraper Autoscout24
# Autoscout24 expose une API JSON quasi-publique
# Couvre France + Belgique + Allemagne proches frontière
# =============================================================

import httpx
from config import CRITERES

SOURCE_ID  = "autoscout24"
SOURCE_NOM = "Autoscout24"
FIABILITE  = 6   # variable selon vendeur

# API Autoscout24 (documentée dans leur app mobile)
API_BASE = "https://www.autoscout24.fr/lst/mercedes-benz/c-300"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept"         : "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer"        : "https://www.autoscout24.fr/",
}


def _construire_params() -> dict:
    return {
        "atype"   : "C",                    # voitures
        "body"    : "8",                    # break (estate)
        "fuel"    : "H",                    # hybride
        "fregfrom": CRITERES["annee_min"],
        "priceto" : CRITERES["budget_max"],
        "kmto"    : CRITERES["km_max"],
        "cy"      : "F",                    # France
        "ustate"  : "U",                    # occasion
        "size"    : 20,
        "page"    : 1,
        "sort"    : "price",
        "desc"    : 0,
    }


def _normaliser_annonce(item: dict) -> dict:
    """Normalise une annonce Autoscout24 au format standard."""

    # Titre
    annee = item.get("firstRegistration", "")[:4] if item.get("firstRegistration") else None
    km    = item.get("mileage")
    titre = f"C300e Break {annee or '?'} · {km or '?'} km"

    # Vendeur
    seller = item.get("seller", {})
    vendeur_nom = seller.get("name", "Pro Autoscout24")
    vendeur_loc = seller.get("location", {})
    ville = vendeur_loc.get("city", "")
    cp    = vendeur_loc.get("zip", "")[:2] if vendeur_loc.get("zip") else ""
    vendeur = f"{vendeur_nom} ({ville} {cp})".strip()

    # Équipements
    equipements = [str(e).lower() for e in item.get("highlights", [])]
    toit = any("panoram" in e or "toit" in e or "dach" in e or "sunroof" in e
               for e in equipements)

    # URL
    ad_id = item.get("id", "")
    url   = f"https://www.autoscout24.fr/annonces/mercedes-benz-classe-c-{ad_id}"

    # Prix
    prix_data = item.get("prices", {}).get("public", {})
    prix = prix_data.get("priceRaw") or item.get("price")

    # Garantie (Autoscout24 ne le garantit pas — on met None)
    garantie = None
    description = str(item.get("description", "")).lower()
    if "garantie" in description or "guarantee" in description:
        # Essayer d'extraire le nombre de mois
        import re
        m = re.search(r"garantie\s+(\d+)\s*mois", description)
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
        "annee"               : int(annee) if annee and annee.isdigit() else None,
        "km"                  : km,
        "puissance_ch"        : item.get("specification", {}).get("power"),
        "toit_ouvrant"        : toit if equipements else None,
        "garantie_mois"       : garantie,
        "premiere_main"       : item.get("previousOwners") == 1,
        "entretien_constructeur": None,
        "couleur"             : item.get("colour"),
        "finition"            : item.get("version"),
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
    params   = _construire_params()
    page     = 1

    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            while True:
                params["page"] = page
                resp = client.get(API_BASE, params=params, headers=HEADERS)
                resp.raise_for_status()

                # Autoscout24 retourne parfois HTML, parfois JSON selon l'Accept
                try:
                    data  = resp.json()
                    items = data.get("listings", data.get("results", []))
                except Exception:
                    # Fallback HTML parsing si JSON non dispo
                    print(f"  ℹ️  Autoscout24 — Réponse non-JSON page {page}, arrêt pagination")
                    break

                if not items:
                    break

                for item in items:
                    try:
                        annonce = _normaliser_annonce(item)
                        if _est_eligible(annonce):
                            annonces.append(annonce)
                    except Exception as e:
                        print(f"  ⚠️  Autoscout24 — Erreur normalisation : {e}")

                # Pagination — max 3 pages pour éviter le rate limiting
                total = data.get("totalCount", 0)
                if page * params["size"] >= total or page >= 3:
                    break
                page += 1

        print(f"✅ Autoscout24 — {len(annonces)} annonces éligibles trouvées")

    except httpx.HTTPStatusError as e:
        print(f"❌ Autoscout24 — Erreur HTTP {e.response.status_code}")
    except Exception as e:
        print(f"❌ Autoscout24 — Erreur : {e}")

    return annonces
