# =============================================================
# scrapers/bmw_certified.py — BMW Premium Selection
# Réseau officiel — Garantie 24 mois constructeur
# -------------------------------------------------------------
# Méthode : API JSON BMW stocklocator (urllib natif)
# Python 3.8 compatible — aucune dépendance externe
# URL : bmw.fr/fr-fr/sl/stocklocator_uc/results
# ⚠️  À tester depuis le NAS (IP résidentielle requise)
# =============================================================

import urllib.request
import urllib.error
import urllib.parse
import json
import re
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SOURCE_ID  = "bmw_certified"
SOURCE_NOM = "BMW Premium Selection"
FIABILITE  = 10

BASE_URL = "https://www.bmw.fr/fr-fr/sl/stocklocator_uc/results"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": "https://www.bmw.fr/",
}


def _build_url(annee_min: int, km_max: int, prix_max: int) -> str:
    filters = {
        "MARKETING_MODEL_RANGE": ["3_G21"],
        "ENGINE":                ["30E"],
        "PRICE":                 [None, prix_max],
        "IS_INSTALLMENT":        False,
        "USED_CAR_MILEAGE":      [0, km_max],
        "REGISTRATION_YEAR":     [annee_min, -1],
    }
    encoded = urllib.parse.quote(json.dumps(filters, separators=(",", ":")))
    return f"{BASE_URL}?filters={encoded}&sorting=PRODUCTION_DATE_DESC"


def _fetch(url: str) -> str:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            logger.warning(f"[BMW Certified] HTTP {e.code} (tentative {attempt+1})")
            if e.code == 403:
                print(f"[BMW Certified] 403 Forbidden — IP bloquée ou WAF actif")
                raise
            if e.code in (429, 503):
                time.sleep(15 * (attempt + 1))
            else:
                raise
        except urllib.error.URLError as e:
            logger.warning(f"[BMW Certified] URLError {e.reason} (tentative {attempt+1})")
            time.sleep(5)
    raise RuntimeError("[BMW Certified] Impossible de charger après 3 tentatives")


def _parse(raw: str, prix_max: int, km_max: int, annee_min: int) -> list:
    annonces = []

    # Tentative JSON direct
    try:
        data = json.loads(raw)
        items = data if isinstance(data, list) else (
            data.get("results") or data.get("vehicles") or data.get("data") or []
        )
        for item in items:
            a = _normaliser(item, prix_max, km_max, annee_min)
            if a:
                annonces.append(a)
        if annonces:
            return annonces
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback : JSON embarqué dans HTML
    for pattern in [
        r'"vehicles"\s*:\s*(\[.*?\])\s*[,}]',
        r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
    ]:
        m = re.search(pattern, raw, re.DOTALL)
        if m:
            try:
                items = json.loads(m.group(1))
                if isinstance(items, dict):
                    items = items.get("results") or items.get("vehicles") or []
                for item in items:
                    a = _normaliser(item, prix_max, km_max, annee_min)
                    if a:
                        annonces.append(a)
                if annonces:
                    return annonces
            except Exception:
                pass

    return annonces


def _normaliser(item: dict, prix_max: int, km_max: int, annee_min: int):
    if not isinstance(item, dict):
        return None

    # Prix
    prix = None
    for k in ["price", "totalPrice", "retailPrice", "finalPrice"]:
        v = item.get(k)
        if isinstance(v, (int, float)) and v > 0:
            prix = int(v)
            break
        elif isinstance(v, dict):
            for sk in ["value", "amount", "gross"]:
                sv = v.get(sk)
                if isinstance(sv, (int, float)) and sv > 0:
                    prix = int(sv)
                    break
            if prix:
                break
    if not prix or prix > prix_max:
        return None

    # Km
    km = None
    for k in ["mileage", "kilometre", "km", "usedCarMileage"]:
        v = item.get(k)
        if isinstance(v, (int, float)) and v >= 0:
            km = int(v)
            break
        elif isinstance(v, dict):
            sv = v.get("value")
            if sv:
                km = int(sv)
                break
    if km and km > km_max:
        return None

    # Année
    annee = None
    for k in ["registrationYear", "firstRegistrationYear", "modelYear", "year"]:
        v = item.get(k)
        if v:
            try:
                y = int(str(v)[:4])
                if 2018 <= y <= 2030:
                    annee = y
                    break
            except (ValueError, TypeError):
                pass
    if annee and annee < annee_min:
        return None

    # ID
    vehicle_id = str(item.get("id") or item.get("vehicleId") or item.get("vin") or "")
    if not vehicle_id:
        return None

    url = (item.get("url") or item.get("detailUrl") or
           f"https://www.bmw.fr/fr-fr/sl/stocklocator_uc/vehicle/{vehicle_id}")

    # Vendeur
    dealer = item.get("dealer") or item.get("seller") or {}
    if isinstance(dealer, dict):
        vendeur = dealer.get("name") or dealer.get("dealerName") or "BMW Premium Selection"
        ville   = dealer.get("city") or dealer.get("location") or ""
        if ville:
            vendeur += f" — {ville}"
    else:
        vendeur = "BMW Premium Selection"

    titre = (item.get("title") or item.get("name") or
             item.get("modelDescription") or "BMW 330e Touring")

    # Toit ouvrant dans équipements
    equips = item.get("features") or item.get("equipment") or item.get("options") or []
    equips_str = " ".join(str(e).lower() for e in equips)
    toit = True if any(w in equips_str for w in ["toit", "panoram", "sunroof"]) else None

    return {
        "id":                     f"bmwcertified_{vehicle_id}",
        "source":                 SOURCE_NOM,
        "source_id":              SOURCE_ID,
        "fiabilite_source":       FIABILITE,
        "titre":                  titre,
        "vendeur":                vendeur,
        "url":                    url,
        "prix":                   prix,
        "annee":                  annee,
        "km":                     km,
        "toit_ouvrant":           toit,
        "garantie_mois":          24,
        "entretien_constructeur": True,
        "premiere_main":          None,
        "carrosserie":            "Touring",
        "motorisation":           "Hybride rechargeable Essence",
        "modele_id":              "bmw_330e",
        "scraped_at":             datetime.now().isoformat(),
    }


def scraper(modele: dict = None) -> list:
    modele_id = (modele or {}).get("id", "")
    if modele_id != "bmw_330e":
        return []

    criteres  = (modele or {}).get("criteres", {})
    annee_min = criteres.get("annee_min", 2023)
    km_max    = criteres.get("km_max",    60000)
    prix_max  = criteres.get("budget_max", 42000)

    url = _build_url(annee_min, km_max, prix_max)
    logger.info(f"[BMW Certified] {url}")

    try:
        raw      = _fetch(url)
        annonces = _parse(raw, prix_max, km_max, annee_min)
    except Exception as e:
        print(f"❌ BMW Certified — {e}")
        return []

    if annonces:
        print(f"✅ BMW Certified — {len(annonces)} annonce(s) éligible(s)")
    else:
        print("❌ BMW Certified — 0 annonce (critères, site bloqué ou structure inconnue)")
        logger.info(f"[BMW Certified] Début réponse : {raw[:300] if raw else 'vide'}")

    return annonces


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    modele_test = {"id": "bmw_330e", "criteres": {"annee_min": 2023, "km_max": 60000, "budget_max": 42000}}
    results = scraper(modele_test)
    print(json.dumps(results, ensure_ascii=False, indent=2))
