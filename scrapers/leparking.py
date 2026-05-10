# =============================================================
# scrapers/leparking.py — Le Parking
# Agrégateur multi-sources — Structure HTML confirmée par tests
# URL : https://www.leparking.fr/voiture-occasion/mercedes-classe-c-break-c-300-e.html
# Structure : li.li-result avec p.prix et holderId dans class
# URL détail : /voiture-occasion/mercedes-classe-c-break-c-300-e-{holderId}.html
# =============================================================

import httpx
import re
from bs4 import BeautifulSoup

SOURCE_ID  = "leparking"
SOURCE_NOM = "Le Parking"
FIABILITE  = 6

BASE_URL   = "https://www.leparking.fr"
SEARCH_URL = f"{BASE_URL}/voiture-occasion/mercedes-classe-c-break-c-300-e.html"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept"         : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection"     : "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest" : "document",
    "Sec-Fetch-Mode" : "navigate",
    "Sec-Fetch-Site" : "none",
}

REGIONS_PRIORITAIRES = [
    "CENTRE", "ILE-DE-FRANCE", "NORMANDIE", "PAYS DE LA LOIRE",
    "GRAND EST", "HAUTS-DE-FRANCE", "BRETAGNE", "OCCITANIE",
    "BOURGOGNE", "AUVERGNE", "NOUVELLE-AQUITAINE", "PACA",
]


def _extraire_annonces(html: str, criteres: dict) -> list:
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
            if not prix or prix < 10000 or prix > budget_max:
                continue

            # Kilométrage
            km = None
            km_match = re.search(r"(\d[\d\s.]+)\s*KM", texte, re.IGNORECASE)
            if km_match:
                km = int(re.sub(r"[\s.]", "", km_match.group(1)))
            if km and km > km_max:
                continue

            # Année — chercher toutes les années et prendre la plus récente < 2027
            annees = [int(a) for a in re.findall(r"\b(20[12][0-9])\b", texte)]
            annees_valides = [a for a in annees if 2019 <= a <= 2026]
            annee = max(annees_valides) if annees_valides else None
            if annee and annee < annee_min:
                continue

            # URL détail
            url = f"{BASE_URL}/voiture-occasion/mercedes-classe-c-break-c-300-e-{holder_id}.html"

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
            titre_match = re.search(r"MERCEDES CLASSE C BREAK C 300 E\s*(.{0,40}?)(?:\s+\d|\s+PRO|\s+FAV|\s*$)", texte.upper())
            finition = titre_match.group(1).strip() if titre_match else ""
            titre = f"C300e Break {finition} {annee or '?'} · {km:,} km".replace(",", " ") if km else f"C300e Break {finition} {annee or '?'}"

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


def scraper(modele: dict = None) -> list:
    """
    Scrape Le Parking pour les C300e Break.
    
    ⚠️  Ce scraper DOIT tourner depuis une IP résidentielle (NAS).
        Il retourne 403 depuis GitHub Actions (IP datacenter).
    """
    criteres = modele.get("criteres", {}) if modele else {}
    annonces = []

    try:
        with httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            resp = client.get(SEARCH_URL)

            if resp.status_code == 403:
                print(f"  ⚠️  Le Parking — 403 (IP datacenter bloquée). Ce scraper doit tourner depuis le NAS.")
                return []

            resp.raise_for_status()
            html = resp.text

        raw = _extraire_annonces(html, criteres)
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
