# =============================================================
# scrapers/spoticar.py — Scraper Spoticar
# Réseau Stellantis — Garantie 12-24 mois kilométrage illimité
# =============================================================

import httpx
import re
from bs4 import BeautifulSoup

SOURCE_ID  = "spoticar"
SOURCE_NOM = "Spoticar"
FIABILITE  = 10

# URL de recherche Spoticar Mercedes Classe C Break
SEARCH_URL = "https://www.spoticar.fr/voitures-occasion/mercedes-classe-c-break"

HEADERS = {
    "User-Agent"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Accept"         : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9",
}


def _extraire_annonces_html(html: str) -> list:
    soup  = BeautifulSoup(html, "lxml")
    cards = soup.select("article.vehicle-card, div.vehicle-card, [data-testid='vehicle-card'], .offer-item")
    return cards


def _normaliser_card(card) -> dict | None:
    try:
        # Titre / modèle
        titre_el = card.select_one("h2, h3, .vehicle-title, .offer-title")
        titre    = titre_el.get_text(strip=True) if titre_el else "C300e Break"

        # Prix
        prix_el  = card.select_one(".price, .vehicle-price, [data-price], .offer-price")
        prix     = None
        if prix_el:
            prix_txt = re.sub(r"[^\d]", "", prix_el.get_text())
            prix     = int(prix_txt) if prix_txt else None

        # Kilométrage
        km_el = card.select_one(".mileage, .km, [data-mileage]")
        km    = None
        if km_el:
            km_txt = re.sub(r"[^\d]", "", km_el.get_text())
            km     = int(km_txt) if km_txt else None

        # Année
        annee_el = card.select_one(".year, .registration, [data-year]")
        annee    = None
        if annee_el:
            m = re.search(r"(20\d{2})", annee_el.get_text())
            if m:
                annee = int(m.group(1))

        # URL annonce
        lien_el = card.select_one("a[href]")
        url     = ""
        if lien_el:
            href = lien_el.get("href", "")
            url  = href if href.startswith("http") else f"https://www.spoticar.fr{href}"

        # Vendeur
        vendeur_el = card.select_one(".dealer, .seller, .garage-name")
        vendeur    = vendeur_el.get_text(strip=True) if vendeur_el else "Spoticar"

        # Toit ouvrant — dans le texte de la card
        texte = card.get_text().lower()
        toit  = True if "toit ouvrant" in texte or "panoram" in texte else None

        return {
            "source"              : SOURCE_NOM,
            "source_id"           : SOURCE_ID,
            "fiabilite_source"    : FIABILITE,
            "titre"               : titre,
            "vendeur"             : vendeur,
            "url"                 : url or SEARCH_URL,
            "prix"                : prix,
            "annee"               : annee,
            "km"                  : km,
            "toit_ouvrant"        : toit,
            "garantie_mois"       : 12,  # minimum Spoticar
            "premiere_main"       : None,
            "entretien_constructeur": None,
        }
    except Exception:
        return None


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
            cards = _extraire_annonces_html(resp.text)

        for card in cards:
            a = _normaliser_card(card)
            if a and _est_eligible(a, criteres):
                annonces.append(a)

        # Si aucune card trouvée → site JS dynamique, on retourne vide proprement
        if not cards:
            print(f"  ℹ️  Spoticar — site JS dynamique, 0 résultats (scraping statique insuffisant)")

        print(f"✅ Spoticar — {len(annonces)} annonces éligibles")

    except httpx.HTTPStatusError as e:
        print(f"❌ Spoticar — HTTP {e.response.status_code}")
    except Exception as e:
        print(f"❌ Spoticar — {e}")

    return annonces
