# =============================================================
# scrapers/mercedes_certified.py — Mercedes-Benz Certified
# Réseau officiel — Garantie 24 mois constructeur
# -------------------------------------------------------------
# Méthode : scraping HTML occasion.mercedes-benz.fr (urllib natif)
# Python 3.8 compatible — aucune dépendance externe
# URL testée le 11/05/2026 — retourne HTML complet sans JS
# =============================================================

import urllib.request
import urllib.error
import urllib.parse
from html.parser import HTMLParser
import re
import json
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SOURCE_ID  = "mercedes_certified"
SOURCE_NOM = "Mercedes-Benz Certified"
FIABILITE  = 10   # réseau officiel constructeur

# URL de base avec tous les filtres encodés
# firrey[min]=2023  → 1ère MEC ≥ 2023
# mileag[max]=60000 → ≤ 60 000 km
# ofprgr[max]=42000 → ≤ 42 000 €
# enginp=5          → hybride rechargeable essence
# eeq29b=1          → toit ouvrant panoramique
# bbodty=stw        → break (station wagon)
# modtyp=c300       → C300
BASE_URL = (
    "https://occasion.mercedes-benz.fr/vehicles"
    "?referrer=home"
    "&view=box"
    "&sorting=acdade"
    "&modtyp=c300"
    "&bbodty=stw"
    "&mileag%5Bmax%5D={km_max}"
    "&ofprgr%5Bmax%5D={prix_max}"
    "&firrey%5Bmin%5D={annee_min}"
    "&enginp=5"
    "&eeq29b=1"
    "&page={page}"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://occasion.mercedes-benz.fr/home",
}


class _MBCertifiedParser(HTMLParser):
    """
    Parse la liste HTML des véhicules MB Certified.
    Stratégie : chaque fiche véhicule est ancrée sur son lien /vehicle?...
    Les données suivantes (prix, km, date MEC, puissance, vendeur) sont
    extraites par pattern matching sur les textes qui suivent.
    """

    def __init__(self):
        super().__init__()
        self.ads = []
        self._cur = {}

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href", "")
        # Lien détail : /vehicle?1262+Mercedes-Benz+C+300+e&vehicle=18904594&...
        m = re.search(r"/vehicle\?([^&\s]+).*?vehicle=(\d+)", href)
        if m:
            raw_id      = m.group(1)      # "1262+Mercedes-Benz+C+300+e"
            vehicle_ref = m.group(2)      # "18904594"
            # Éviter d'écraser une fiche en cours si même lien répété
            if self._cur.get("vehicle_ref") == vehicle_ref:
                return
            # Sauvegarder la fiche précédente si complète
            self._flush()
            internal_num = raw_id.split("+")[0]
            titre = " ".join(raw_id.split("+")[1:])
            self._cur = {
                "vehicle_id":  internal_num,
                "vehicle_ref": vehicle_ref,
                "titre":       titre,
                "url": (
                    f"https://occasion.mercedes-benz.fr/vehicle"
                    f"?{raw_id}&vehicle={vehicle_ref}&referrer=vehicles"
                ),
            }

    def handle_data(self, data):
        data = data.strip()
        if not data or "vehicle_ref" not in self._cur:
            return

        # Prix : "39 750 €"
        if "€" in data:
            prix_str = re.sub(r"[^\d]", "", data)
            if prix_str and "prix" not in self._cur:
                try:
                    prix = int(prix_str)
                    if 10_000 < prix < 200_000:
                        self._cur["prix"] = prix
                except ValueError:
                    pass

        # Kilométrage : "54 611 km"
        m = re.match(r"^([\d\s\u202f]+)\s*km$", data)
        if m and "km" not in self._cur:
            try:
                self._cur["km"] = int(re.sub(r"\D", "", m.group(1)))
            except ValueError:
                pass

        # Date MEC : "31.08.2023"
        m = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})$", data)
        if m and "annee" not in self._cur:
            self._cur["annee"]    = int(m.group(3))
            self._cur["date_mec"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

        # Puissance : "230 kW (313 CH)"
        m = re.match(r"^\d+\s*kW\s*\((\d+)\s*CH\)$", data)
        if m and "puissance_ch" not in self._cur:
            self._cur["puissance_ch"] = int(m.group(1))

        # Vendeur : "BPM CARS ALENÇON 61000 CERISÉ"
        m = re.match(r"^([A-ZÉÈÀÂÙÎÔÊÄËÏÜÙŒÇ][A-ZÉÈÀÂÙÎÔÊÄËÏÜÙŒÇ0-9\s\-\'\.]+)\s+(\d{5})\s+(.+)$", data)
        if m and "vendeur" not in self._cur and len(data) > 8:
            self._cur["vendeur"] = data
            self._cur["cp"]      = m.group(2)
            self._cur["ville"]   = m.group(3).strip()

    def _flush(self):
        """Sauvegarde la fiche courante si elle contient les champs minimaux."""
        if (
            self._cur.get("vehicle_ref")
            and self._cur.get("prix")
            and self._cur.get("km")
            and self._cur.get("annee")
        ):
            refs = [a["vehicle_ref"] for a in self.ads]
            if self._cur["vehicle_ref"] not in refs:
                self.ads.append(dict(self._cur))
        self._cur = {}

    def close(self):
        self._flush()
        super().close()


def _fetch(url: str) -> str:
    """Télécharge une page avec 3 tentatives et backoff."""
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            logger.warning(f"[MB Certified] HTTP {e.code} (tentative {attempt + 1}) — {url}")
            if e.code in (429, 503):
                time.sleep(15 * (attempt + 1))
            else:
                raise
        except urllib.error.URLError as e:
            logger.warning(f"[MB Certified] URLError {e.reason} (tentative {attempt + 1})")
            time.sleep(5)
    raise RuntimeError(f"[MB Certified] Impossible de charger {url} après 3 tentatives")


def _total_annonces(html: str) -> int:
    m = re.search(r"(\d+)\s+véhicule", html)
    return int(m.group(1)) if m else 0


def scraper(modele: dict = None) -> list:
    """
    Point d'entrée principal — interface identique aux autres scrapers du projet.
    Accepte un dict `modele` avec une clé `criteres` (annee_min, km_max, budget_max).
    Retourne une liste de dicts normalisés compatibles seen_ads.json.
    """
    criteres  = (modele or {}).get("criteres", {})
    annee_min = criteres.get("annee_min", 2023)
    km_max    = criteres.get("km_max",    60000)
    prix_max  = criteres.get("budget_max", 42000)

    annonces = []
    page     = 1

    while True:
        url = BASE_URL.format(
            annee_min=annee_min,
            km_max=km_max,
            prix_max=prix_max,
            page=page,
        )
        logger.info(f"[MB Certified] Page {page} — {url}")

        try:
            html = _fetch(url)
        except RuntimeError as e:
            logger.error(str(e))
            break

        if page == 1:
            total = _total_annonces(html)
            logger.info(f"[MB Certified] {total} véhicule(s) annoncé(s) par le site")
            if total == 0:
                logger.info("[MB Certified] Aucun résultat pour ces critères.")
                break

        parser = _MBCertifiedParser()
        parser.feed(html)
        parser.close()
        page_ads = parser.ads

        if not page_ads:
            logger.info(f"[MB Certified] Page {page} vide — fin pagination")
            break

        # Normalisation au format car-watch
        for ad in page_ads:
            ad_id = f"mbcertified_{ad['vehicle_ref']}"
            annonces.append({
                # Identification
                "id":                     ad_id,
                "source":                 SOURCE_NOM,
                "source_id":              SOURCE_ID,
                "fiabilite_source":       FIABILITE,
                # Annonce
                "titre":                  ad.get("titre", "Mercedes C300e Break"),
                "vendeur":                ad.get("vendeur", f"MB Certified — {ad.get('ville', '')}").strip(),
                "url":                    ad.get("url"),
                # Données chiffrées
                "prix":                   ad.get("prix"),
                "annee":                  ad.get("annee"),
                "km":                     ad.get("km"),
                "date_mec":               ad.get("date_mec"),
                "puissance_ch":           ad.get("puissance_ch", 313),
                # Équipements / garantie — certitudes issues des filtres URL
                "toit_ouvrant":           True,   # filtre eeq29b=1 appliqué
                "garantie_mois":          24,     # MB Certified = 2 ans systématiquement
                "entretien_constructeur": True,   # réseau agréé MB
                "premiere_main":          None,   # non disponible sur le site
                # Meta
                "carrosserie":            "Break",
                "motorisation":           "Hybride rechargeable Essence",
                "scraped_at":             datetime.now().isoformat(),
            })

        logger.info(f"[MB Certified] Page {page} : {len(page_ads)} annonce(s)")

        # MB Certified affiche ~12 résultats par page max
        if len(page_ads) < 12:
            break
        page += 1
        time.sleep(2)

    if annonces:
        print(f"✅ MB Certified — {len(annonces)} annonce(s) éligible(s)")
    else:
        print("❌ MB Certified — 0 annonce (critères trop stricts ou site indisponible)")

    return annonces


# ---------------------------------------------------------------------------
# Test standalone : python3 scrapers/mercedes_certified.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    modele_test = {
        "criteres": {
            "annee_min":  2023,
            "km_max":     60000,
            "budget_max": 42000,
        }
    }
    results = scraper(modele_test)
    print(json.dumps(results, ensure_ascii=False, indent=2))
