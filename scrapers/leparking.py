# =============================================================
# scrapers/leparking.py — Le Parking
# Agrégateur multi-sources — Structure HTML confirmée par tests
# URL : https://www.leparking.fr/voiture-occasion/mercedes-classe-c-break-c-300-e.html
# Structure : li.li-result avec p.prix et holderId dans class
# URL détail : /voiture-occasion/mercedes-classe-c-break-c-300-e-{holderId}.html
# =============================================================

import re
import urllib.request
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

SOURCE_ID  = "leparking"
SOURCE_NOM = "Le Parking"
FIABILITE  = 6

BASE_URL   = "https://www.leparking.fr"

# URLs par modèle
SEARCH_URLS = {
    "mercedes_c300e" : f"{BASE_URL}/voiture-occasion/mercedes-classe-c-break-c-300-e.html",
    "bmw_3series"    : f"{BASE_URL}/voiture-occasion/bmw-serie-3-break-330e.html",
    "audi_a3"        : f"{BASE_URL}/voiture-occasion/audi-a3-sportback.html",
    "mercedes_a"     : f"{BASE_URL}/voiture-occasion/mercedes-classe-a.html",
}
SEARCH_URL = SEARCH_URLS["mercedes_c300e"]  # fallback

HEADERS = {
    "User-Agent"             : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Accept"                 : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language"        : "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding"        : "gzip, deflate, br",
    "Cache-Control"          : "max-age=0",
    "Sec-Fetch-Dest"         : "document",
    "Sec-Fetch-Mode"         : "navigate",
    "Sec-Fetch-Site"         : "none",
    "Sec-Fetch-User"         : "?1",
    "Upgrade-Insecure-Requests": "1",
    "sec-ch-ua"              : '"Google Chrome";v="147", "Chromium";v="147", "Not=A?Brand";v="24"',
    "sec-ch-ua-mobile"       : "?0",
    "sec-ch-ua-platform"     : '"Windows"',
}

REGIONS_PRIORITAIRES = [
    "CENTRE", "ILE-DE-FRANCE", "NORMANDIE", "PAYS DE LA LOIRE",
    "GRAND EST", "HAUTS-DE-FRANCE", "BRETAGNE", "OCCITANIE",
    "BOURGOGNE", "AUVERGNE", "NOUVELLE-AQUITAINE", "PACA",
]


def _extraire_annonces(html: str, criteres: dict, modele_nom: str = "Break") -> list:
    """Parse le HTML du Parking et extrait les annonces."""
    soup    = BeautifulSoup(html, "lxml")
    blocs   = soup.select("li.li-result")
    annonces = []

    annee_min  = criteres.get("annee_min", 2023)
    budget_max = criteres.get("budget_max", 42000)
    km_max     = criteres.get("km_max", 65000)

    for li in blocs:
        try:
            # ID de l'annonce (holderId dans la classe CSS)
            class_str = " ".join(li.get("class", []))
            holder_match = re.search(r"holder-(\d+)", class_str)
            if not holder_match:
                continue
            holder_id = holder_match.group(1)

            # Texte complet du bloc
            texte = li.get_text(" ", strip=True)

            # Prix
            prix_el = li.select_one("p.prix")
            if not prix_el:
                continue
            prix_txt = re.sub(r"[^\d]", "", prix_el.get_text())
            prix = int(prix_txt) if prix_txt else None
            prix_min = max(500, budget_max // 20)  # min dynamique selon budget
            if not prix or prix < prix_min or prix > budget_max:
                continue

            # Kilométrage
            km = None
            km_match = re.search(r"(\d[\d\s.]+)\s*KM", texte, re.IGNORECASE)
            if km_match:
                km = int(re.sub(r"[\s.]", "", km_match.group(1)))
            if km and km > km_max:
                continue

            # Année — chercher toutes les années et prendre la plus récente < 2027
            annee = None
            # Chercher "Année XXXX" en priorité (millésime réel)
            annee_label = re.search(r"Ann[eé]+e?\s*[:\-]?\s*(20[12][0-9])", texte, re.IGNORECASE)
            if annee_label:
                annee = int(annee_label.group(1))
            if not annee:
                # Fallback : toutes les années dans le texte sauf 2025/2026 (dates publication)
                toutes = [int(a) for a in re.findall(r"\b(20[12][0-9])\b", texte)]
                annee_min_fallback = max(2014, annee_min - 1)
                valides = [a for a in toutes if annee_min_fallback <= a <= 2026]
                annee = max(valides) if valides else None
            if annee and annee < annee_min:
                continue

            # URL détail — sera remplacée par l'URL réelle après fetch détail
            url = f"{BASE_URL}/voiture-occasion/placeholder-{holder_id}.html"

            # Toit ouvrant
            texte_lower = texte.lower()
            toit = True if "toit ouvrant" in texte_lower or "panoram" in texte_lower else None

            # Vendeur professionnel
            is_pro = "PROFESSIONNEL" in texte.upper()

            # Garantie mentionnée
            garantie = None
            g_match = re.search(r"garantie\s+(\d+)\s*mois", texte_lower)
            if g_match:
                garantie = int(g_match.group(1))

            # Région
            region = next((r for r in REGIONS_PRIORITAIRES if r in texte.upper()), "")

            # Finition / description
            finition = ""
            titre = f"{modele_nom} {finition} {annee or '?'} · {km:,} km".replace(",", " ") if km else f"{modele_nom} {finition} {annee or '?'}"

            annonces.append({
                "source"              : SOURCE_NOM,
                "source_id"           : SOURCE_ID,
                "fiabilite_source"    : FIABILITE,
                "titre"               : titre.strip(),
                "vendeur"             : f"Pro Le Parking ({region})" if is_pro else f"Particulier Le Parking ({region})",
                "url"                 : url,
                "prix"                : prix,
                "annee"               : annee,
                "km"                  : km,
                "toit_ouvrant"        : toit,
                "garantie_mois"       : garantie,
                "premiere_main"       : None,
                "entretien_constructeur": None,
                "region"              : region,
                "is_pro"              : is_pro,
                "holder_id"           : holder_id,
            })

        except Exception as e:
            continue

    return annonces


def _est_eligible(annonce: dict, criteres: dict) -> bool:
    """Vérification finale d'éligibilité."""
    if annonce.get("annee") and annonce["annee"] < criteres.get("annee_min", 2023):
        return False
    if annonce.get("km") and annonce["km"] > criteres.get("km_max", 65000):
        return False
    if annonce.get("prix") and annonce["prix"] > criteres.get("budget_max", 42000):
        return False
    return True



def _fetch_annee_detail(holder_id, headers, detail_url_pattern: str = None):
    """Récupère l année réelle sur la page détail de l annonce."""
    import time
    if detail_url_pattern:
        url = detail_url_pattern.format(holder_id=holder_id)
    else:
        url = f"{BASE_URL}/voiture-occasion/mercedes-classe-c-break-c-300-e-{holder_id}.html"
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=10)
        raw  = resp.read()
        import gzip as gz
        html = gz.decompress(raw).decode("utf-8", errors="ignore") if resp.info().get("Content-Encoding") == "gzip" else raw.decode("utf-8", errors="ignore")
        m = re.search(r'Ann[eé]+e?\s*[:\-]?\s*(20[12][0-9])', html, re.IGNORECASE)
        time.sleep(0.3)  # politesse
        return int(m.group(1)) if m else None
    except Exception:
        return None

# Patterns URL détail par modèle
DETAIL_URL_PATTERNS = {
    "mercedes_c300e" : BASE_URL + "/voiture-occasion/mercedes-classe-c-break-c-300-e-{holder_id}.html",
    "bmw_3series"    : BASE_URL + "/voiture-occasion/bmw-serie-3-break-330e-{holder_id}.html",
    "audi_a3"        : BASE_URL + "/voiture-occasion/audi-a3-sportback-{holder_id}.html",
    "mercedes_a"     : BASE_URL + "/voiture-occasion/mercedes-classe-a-{holder_id}.html",
}

def scraper(modele: dict = None) -> list:
    """
    Scrape Le Parking — supporte Mercedes C300e et BMW 330e.
    ⚠️  Ce scraper DOIT tourner depuis une IP résidentielle (NAS).
    """
    criteres   = modele.get("criteres", {}) if modele else {}
    modele_id  = modele.get("id", "mercedes_c300e") if modele else "mercedes_c300e"
    modele_nom = modele.get("nom", "Break") if modele else "Break"
    search_url = SEARCH_URLS.get(modele_id, SEARCH_URL)
    detail_pat = DETAIL_URL_PATTERNS.get(modele_id)
    annonces = []

    try:
        req = urllib.request.Request(search_url, headers=HEADERS)
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            raw = resp.read()
            # Décoder gzip si nécessaire
            if resp.info().get("Content-Encoding") == "gzip":
                import gzip as gzip_mod
                html = gzip_mod.decompress(raw).decode("utf-8", errors="ignore")
            else:
                html = raw.decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as http_err:
            if http_err.code == 403:
                print(f"  ⚠️  Le Parking — 403. Vérifier les headers User-Agent.")
                return []
            raise

        if HAS_BS4:
            raw = _extraire_annonces(html, criteres, modele_nom)
        else:
            print(f"  ℹ️  Le Parking — BeautifulSoup absent, parsing regex")
            raw = _extraire_annonces(html, criteres, modele_nom)

        # Enrichir avec l'année réelle depuis la page détail + corriger l'URL
        enrichies = []
        for a in raw:
            hid = a.get("holder_id", "")
            if hid:
                # Corriger l'URL avec le bon pattern
                if detail_pat:
                    a["url"] = detail_pat.format(holder_id=hid)
                annee_reelle = _fetch_annee_detail(hid, HEADERS, detail_pat)
                if annee_reelle:
                    a["annee"] = annee_reelle
                    annee_min_c = criteres.get("annee_min", 2023)
                    if annee_reelle < annee_min_c:
                        continue
            enrichies.append(a)
        raw = enrichies
        annonces = [a for a in raw if _est_eligible(a, criteres)]

        # Dédupliquer par holder_id
        seen = set()
        dedup = []
        for a in annonces:
            hid = a.get("holder_id", "")
            if hid not in seen:
                seen.add(hid)
                dedup.append(a)

        print(f"✅ Le Parking — {len(dedup)} annonces éligibles ({len(raw)} brutes)")
        return dedup

    except httpx.HTTPStatusError as e:
        print(f"❌ Le Parking — HTTP {e.response.status_code}")
    except Exception as e:
        print(f"❌ Le Parking — {e}")

    return []
