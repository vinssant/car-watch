# =============================================================
# scrapers/autoscout24_nas.py — Autoscout24 via IP résidentielle
# URL confirmée par tests NAS : /lst/mercedes-benz/c-300
# Retourne les C300 hybrides (Électrique/Essence) break uniquement
# =============================================================

import re
try:
    import httpx
    USE_HTTPX = True
except ImportError:
    import urllib.request
    USE_HTTPX = False

import json

SOURCE_ID  = "autoscout24_nas"
SOURCE_NOM = "Autoscout24"
FIABILITE  = 6

# URL confirmée par tests — retourne C300 hybrides uniquement
SEARCH_URL = "https://www.autoscout24.fr/lst/mercedes-benz/c-300"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept"         : "text/html,application/xhtml+xml",
}

BREAKS_TYPES = ["wagon", "t-modell", "estate", "combi", "break", "sw"]


def _fetch_html(url: str) -> str:
    if USE_HTTPX:
        with httpx.Client(timeout=20, follow_redirects=True, headers=HEADERS) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text
    else:
        req = urllib.request.Request(url, headers=HEADERS)
        resp = urllib.request.urlopen(req, timeout=20)
        return resp.read().decode("utf-8", errors="ignore")


def _extraire_listings(html: str) -> list:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
        return data.get("props", {}).get("pageProps", {}).get("listings", [])
    except Exception:
        return []


def _normaliser(item: dict):
    v     = item.get("vehicle", {}) or {}
    p     = item.get("price", {}) or {}
    s     = item.get("seller", {}) or {}
    loc   = s.get("location", {}) or {}

    # Filtrer uniquement breaks — AS24 met le type dans variant
    variant = (v.get("variant") or "").lower()
    vtype   = (v.get("type") or "").lower()
    is_break = any(t in variant for t in BREAKS_TYPES) or any(t in vtype for t in BREAKS_TYPES)
    if not is_break:
        return None

    # Filtrer uniquement hybrides
    fuel = v.get("fuel") or ""
    if "lectrique" not in fuel and "hybride" not in fuel.lower():
        return None

    # Prix
    prix_fmt = p.get("priceFormatted", "")
    prix_raw = re.sub(r"[^\d]", "", prix_fmt)
    prix     = int(prix_raw) if prix_raw else None

    # Km
    km_raw = v.get("mileageInKm") or ""
    km     = int(re.sub(r"[^\d]", "", str(km_raw))) if km_raw else None

    # Année — firstRegistration souvent vide sur AS24 FR
    # Chercher dans l'URL de l'annonce ou le titre
    annee   = None
    reg     = v.get("firstRegistration") or v.get("modelYear") or ""
    m_year  = re.search(r"(20\d{2})", str(reg))
    if m_year:
        annee = int(m_year.group(1))
    if not annee:
        # Chercher dans l'URL
        url_path = item.get("url", "")
        m_url = re.search(r"-(202[0-9])-", url_path)
        if m_url:
            annee = int(m_url.group(1))

    # URL
    url_path = item.get("url", "")
    url      = f"https://www.autoscout24.fr{url_path}" if url_path else ""

    # Toit ouvrant — dans l'URL ou titre
    texte_lower = url_path.lower() + (v.get("variant") or "").lower()
    toit = True if "panoram" in texte_lower or "toit" in texte_lower or "sunroof" in texte_lower else None

    # Vendeur
    ville   = loc.get("city", "")
    cp      = str(loc.get("zip", ""))[:2]
    vendeur = f"{s.get('name', 'Pro AS24')}"
    if ville:
        vendeur += f" ({ville} {cp})".rstrip()

    # Garantie dans description
    desc     = (item.get("description") or "").lower()
    garantie = None
    g        = re.search(r"garantie\s+(\d+)\s*mois", desc)
    if g:
        garantie = int(g.group(1))

    titre = f"C300e Break {annee or '?'} · {km:,} km".replace(",", " ") if km else f"C300e Break {annee or '?'}"

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
        "premiere_main"       : v.get("previousOwners") == 1,
        "entretien_constructeur": None,
    }


def _est_eligible(a: dict, criteres: dict) -> bool:
    # Si année inconnue on garde l'annonce (données AS24 incomplètes)
    if a.get("annee") and a["annee"] < criteres.get("annee_min", 2023):
        return False
    if a.get("km") and a["km"] > criteres.get("km_max", 65000):
        return False
    if a.get("prix") and a["prix"] > criteres.get("budget_max", 42000):
        return False
    return True


def scraper(modele: dict = None) -> list:
    """
    Scrape Autoscout24 C300 depuis le NAS (IP résidentielle).
    URL confirmée : /lst/mercedes-benz/c-300
    Filtre breaks hybrides en Python.
    """
    criteres   = modele.get("criteres", {}) if modele else {}
    annee_min  = criteres.get("annee_min", 2023)
    budget_max = criteres.get("budget_max", 42000)
    km_max     = criteres.get("km_max", 65000)

    url = (f"{SEARCH_URL}?fregfrom={annee_min}&priceto={budget_max}"
           f"&kmto={km_max}&ustate=U&cy=F&sort=price&desc=0")

    annonces = []
    try:
        html     = _fetch_html(url)
        listings = _extraire_listings(html)

        for item in listings:
            a = _normaliser(item)
            if a and _est_eligible(a, criteres):
                annonces.append(a)

        print(f"✅ Autoscout24 NAS — {len(annonces)} annonces éligibles ({len(listings)} brutes)")

    except Exception as e:
        print(f"❌ Autoscout24 NAS — {e}")

    return annonces
