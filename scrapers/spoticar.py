# =============================================================
# scrapers/spoticar.py — Spoticar (réseau Stellantis)
# -------------------------------------------------------------
# Méthode : scraping HTML www.spoticar.fr (urllib natif)
# Python 3.8 compatible — aucune dépendance externe
# ⚠️  Toit ouvrant NON filtrable côté URL → détection en post-traitement
#     sur la page détail de chaque annonce éligible
# =============================================================

import urllib.request
import urllib.error
from html.parser import HTMLParser
import re
import json
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SOURCE_ID  = "spoticar"
SOURCE_NOM = "Spoticar"
FIABILITE  = 9   # réseau agréé constructeur (Stellantis)

# URL liste — les filtres sont indexés [0]..[N], extensibles
# filters[0][category]   = break
# filters[1][max_km]     = 60001
# filters[2][max_price]  = 42000
# filters[3][brand]      = mercedes
# filters[4][model]      = classe c
# filters[5][energy]     = hybride rechargeable
# filters[6][min_year]   = 2023
BASE_LIST_URL = (
    "https://www.spoticar.fr/voitures-occasion"
    "?page={page}"
    "&filters%5B0%5D%5Bcategory%5D=break"
    "&filters%5B1%5D%5Bmax_km%5D={km_max}"
    "&filters%5B2%5D%5Bmax_price%5D={prix_max}"
    "&filters%5B3%5D%5Bbrand%5D=mercedes"
    "&filters%5B4%5D%5Bmodel%5D=classe%20c"
    "&filters%5B5%5D%5Benergy%5D=hybride%20rechargeable"
    "&filters%5B6%5D%5Bmin_year%5D={annee_min}"
)

BASE_DETAIL_URL = "https://www.spoticar.fr"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.spoticar.fr/",
}


# ---------------------------------------------------------------------------
# Parser — page de liste
# ---------------------------------------------------------------------------

class _SpoticarListParser(HTMLParser):
    """
    Extrait les fiches véhicule de la page de résultats Spoticar.
    Structure attendue (HTML Spoticar) :
      <a href="/voitures-occasion/mercedes-classe-c-...-1203874375" ...>
        ...données de la carte...
      </a>
    Les données sont dans des attributs data-* ou dans le texte des balises.
    Le parser tente les deux stratégies.
    """

    def __init__(self):
        super().__init__()
        self.ads       = []
        self._cur      = {}
        self._in_card  = False
        self._depth    = 0
        self._card_start_depth = 0

    # -- Pattern slug annonce : /voitures-occasion/{titre}-{id_numerique}
    _SLUG_RE = re.compile(
        r"/voitures-occasion/(mercedes[-\w]+-(\d{7,12}))$"
    )

    def handle_starttag(self, tag, attrs):
        self._depth += 1
        attrs_dict = dict(attrs)

        # Détection d'une carte via le lien slug
        href = attrs_dict.get("href", "")
        m = self._SLUG_RE.match(href)
        if m and tag == "a":
            if self._in_card:
                self._flush()
            self._in_card = True
            self._card_start_depth = self._depth
            slug   = m.group(1)
            ad_id  = m.group(2)
            self._cur = {
                "ad_id": ad_id,
                "slug":  slug,
                "url":   BASE_DETAIL_URL + href,
            }

        if not self._in_card:
            return

        # Données en attributs data-* (souvent présentes sur les cards)
        for attr, val in attrs_dict.items():
            if not val:
                continue
            al = attr.lower()
            if al in ("data-price", "data-vehicle-price"):
                try:
                    self._cur.setdefault("prix", int(re.sub(r"\D", "", val)))
                except ValueError:
                    pass
            elif al in ("data-mileage", "data-km", "data-vehicle-mileage"):
                try:
                    self._cur.setdefault("km", int(re.sub(r"\D", "", val)))
                except ValueError:
                    pass
            elif al in ("data-year", "data-vehicle-year", "data-registration-year"):
                try:
                    self._cur.setdefault("annee", int(val[:4]))
                except ValueError:
                    pass
            elif al in ("data-title", "data-vehicle-title", "data-name"):
                self._cur.setdefault("titre", val.strip())
            elif al in ("data-city", "data-dealer-city", "data-location"):
                self._cur.setdefault("ville", val.strip())
            elif al in ("data-dealer", "data-dealer-name"):
                self._cur.setdefault("vendeur", val.strip())

    def handle_data(self, data):
        if not self._in_card:
            return
        data = data.strip()
        if not data:
            return

        # Prix : "39 990 €" ou "39 990€"
        if "€" in data and "prix" not in self._cur:
            prix_str = re.sub(r"[^\d]", "", data)
            if prix_str:
                try:
                    p = int(prix_str)
                    if 5_000 < p < 150_000:
                        self._cur["prix"] = p
                except ValueError:
                    pass

        # Kilométrage : "54 611 km" ou "54611km"
        m = re.match(r"^([\d\s\u202f]+)\s*km$", data, re.IGNORECASE)
        if m and "km" not in self._cur:
            try:
                self._cur["km"] = int(re.sub(r"\D", "", m.group(1)))
            except ValueError:
                pass

        # Année / date MEC : "2023" ou "08/2023" ou "31/08/2023"
        if "annee" not in self._cur:
            m = re.search(r"\b(202[0-9])\b", data)
            if m:
                self._cur["annee"] = int(m.group(1))

        # Puissance
        m = re.search(r"(\d{2,3})\s*ch", data, re.IGNORECASE)
        if m and "puissance_ch" not in self._cur:
            self._cur["puissance_ch"] = int(m.group(1))

        # Toit ouvrant (parfois mentionné dans le résumé équipements)
        if "toit_ouvrant" not in self._cur:
            dl = data.lower()
            if any(k in dl for k in ("toit ouvrant", "panoram", "sunroof", "toit vitré")):
                self._cur["toit_ouvrant"] = True

        # Ville / concession (texte court ressemblant à une ville)
        if "ville" not in self._cur and 3 < len(data) < 50:
            if re.match(r"^[A-ZÉÈÀÂÙ][a-zéèàâùîôêäëïü\-\s]+$", data):
                self._cur.setdefault("ville_candidate", data)

    def handle_endtag(self, tag):
        if self._in_card and self._depth == self._card_start_depth:
            self._flush()
            self._in_card = False
        self._depth -= 1

    def _flush(self):
        if self._cur.get("ad_id") and self._cur.get("prix") and self._cur.get("km"):
            if "ville" not in self._cur and "ville_candidate" in self._cur:
                self._cur["ville"] = self._cur.pop("ville_candidate")
            ids = [a["ad_id"] for a in self.ads]
            if self._cur["ad_id"] not in ids:
                self.ads.append(dict(self._cur))
        self._cur = {}

    def close(self):
        self._flush()
        super().close()


# ---------------------------------------------------------------------------
# Parser — page détail (toit ouvrant + garantie)
# ---------------------------------------------------------------------------

class _SpoticarDetailParser(HTMLParser):
    """
    Extrait les équipements et la garantie depuis la fiche détail.
    Cherche : toit ouvrant / panoramique, garantie N mois/ans.
    """

    def __init__(self):
        super().__init__()
        self.toit_ouvrant  = False
        self.garantie_mois = None
        self.titre         = None
        self.vendeur       = None
        self._in_title     = False

    _TOIT_KW   = re.compile(r"toit.{0,10}(ouvrant|panoram|vitré)", re.IGNORECASE)
    _GARANTIE  = re.compile(r"garantie\D{0,15}(\d+)\s*(mois|an)", re.IGNORECASE)

    def handle_data(self, data):
        raw = data.strip()
        if not raw:
            return

        if self._TOIT_KW.search(raw):
            self.toit_ouvrant = True

        m = self._GARANTIE.search(raw)
        if m and self.garantie_mois is None:
            val  = int(m.group(1))
            unit = m.group(2).lower()
            self.garantie_mois = val * 12 if unit.startswith("an") else val

    def close(self):
        super().close()


# ---------------------------------------------------------------------------
# Helpers réseau
# ---------------------------------------------------------------------------

def _fetch(url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            logger.warning(f"[Spoticar] HTTP {e.code} (tentative {attempt + 1}) — {url}")
            if e.code in (429, 503):
                time.sleep(15 * (attempt + 1))
            elif e.code == 403:
                # Cloudflare / WAF — on abandonne vite
                logger.error(f"[Spoticar] 403 Forbidden — IP bloquée ou WAF actif")
                raise
            else:
                raise
        except urllib.error.URLError as e:
            logger.warning(f"[Spoticar] URLError {e.reason} (tentative {attempt + 1})")
            time.sleep(5)
    raise RuntimeError(f"[Spoticar] Impossible de charger {url} après {retries} tentatives")


def _total_annonces(html: str) -> int:
    # "X voiture(s) trouvée(s)" ou "X résultats"
    m = re.search(r"(\d+)\s+(?:voiture|résultat|annonce)", html, re.IGNORECASE)
    return int(m.group(1)) if m else -1  # -1 = inconnu mais on continue


def _fetch_detail(url: str) -> dict:
    """Récupère toit ouvrant + garantie depuis la page détail."""
    try:
        html   = _fetch(url)
        parser = _SpoticarDetailParser()
        parser.feed(html)
        parser.close()
        return {
            "toit_ouvrant":  parser.toit_ouvrant,
            "garantie_mois": parser.garantie_mois,
        }
    except Exception as e:
        logger.warning(f"[Spoticar] Impossible de lire le détail {url} : {e}")
        return {"toit_ouvrant": None, "garantie_mois": None}


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def scraper(modele: dict = None) -> list:
    """
    Interface identique aux autres scrapers du projet.
    Accepte un dict `modele` avec une clé `criteres`.
    Retourne une liste de dicts normalisés compatibles seen_ads.json.

    ⚠️  Le toit ouvrant n'est pas filtrable dans l'URL Spoticar.
        → détecté en post-traitement sur la page détail de chaque annonce.
        → les annonces sans toit ouvrant confirmé sont retournées avec
          toit_ouvrant=False/None et laissées au scorer pour décision.
    """
    criteres  = (modele or {}).get("criteres", {})
    annee_min = criteres.get("annee_min", 2023)
    km_max    = criteres.get("km_max",    60000)
    prix_max  = criteres.get("budget_max", 42000)
    # Filtre toit ouvrant appliqué en post-traitement ?
    # Par défaut on retourne toutes les annonces et on laisse le scorer décider.
    # Mettre à True pour ne retourner QUE les annonces avec toit confirmé.
    filtrer_toit = criteres.get("toit_ouvrant_strict", False)

    annonces = []
    page     = 1

    while True:
        url = BASE_LIST_URL.format(
            page=page,
            km_max=km_max + 1,   # Spoticar utilise < donc +1
            prix_max=prix_max,
            annee_min=annee_min,
        )
        logger.info(f"[Spoticar] Page {page} — {url}")

        try:
            html = _fetch(url)
        except Exception as e:
            logger.error(f"[Spoticar] Abandon : {e}")
            break

        if page == 1:
            total = _total_annonces(html)
            if total == 0:
                logger.info("[Spoticar] Aucun résultat.")
                break
            logger.info(f"[Spoticar] ~{total} annonce(s) trouvée(s)")

        parser = _SpoticarListParser()
        parser.feed(html)
        parser.close()
        page_ads = parser.ads

        if not page_ads:
            logger.info(f"[Spoticar] Page {page} vide — fin pagination")
            break

        logger.info(f"[Spoticar] Page {page} : {len(page_ads)} annonce(s) parsées")

        for ad in page_ads:
            # Récupération du détail pour toit ouvrant + garantie
            time.sleep(1)   # politesse entre les détails
            detail = _fetch_detail(ad["url"])

            toit      = detail.get("toit_ouvrant")
            garantie  = detail.get("garantie_mois") or 12  # défaut Spoticar ~12 mois

            # Filtre strict toit ouvrant si demandé
            if filtrer_toit and not toit:
                logger.info(f"[Spoticar] Annonce {ad['ad_id']} ignorée — pas de toit ouvrant")
                continue

            ad_id = f"spoticar_{ad['ad_id']}"
            annonces.append({
                # Identification
                "id":                     ad_id,
                "source":                 SOURCE_NOM,
                "source_id":              SOURCE_ID,
                "fiabilite_source":       FIABILITE,
                # Annonce
                "titre":                  ad.get("titre") or f"Mercedes Classe C Break {ad.get('annee', '')}",
                "vendeur":                ad.get("vendeur") or ad.get("ville") or "Spoticar",
                "url":                    ad.get("url"),
                # Données chiffrées
                "prix":                   ad.get("prix"),
                "annee":                  ad.get("annee"),
                "km":                     ad.get("km"),
                "puissance_ch":           ad.get("puissance_ch"),
                # Équipements
                "toit_ouvrant":           toit,       # None = non détecté
                "garantie_mois":          garantie,
                "entretien_constructeur": True,       # réseau agréé Stellantis
                "premiere_main":          None,
                # Meta
                "carrosserie":            "Break",
                "motorisation":           "Hybride rechargeable",
                "scraped_at":             datetime.now().isoformat(),
            })

        # Spoticar affiche généralement 12 ou 24 résultats par page
        if len(page_ads) < 12:
            break
        page += 1
        time.sleep(2)

    if annonces:
        print(f"✅ Spoticar — {len(annonces)} annonce(s) éligible(s)")
    else:
        print("❌ Spoticar — 0 annonce (critères trop stricts, site bloqué ou WAF actif)")

    return annonces


# ---------------------------------------------------------------------------
# Test standalone : python3 scrapers/spoticar.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    modele_test = {
        "criteres": {
            "annee_min":           2023,
            "km_max":              60000,
            "budget_max":          42000,
            "toit_ouvrant_strict": False,   # True = ne garder que les toits confirmés
        }
    }
    results = scraper(modele_test)
    print(json.dumps(results, ensure_ascii=False, indent=2))
