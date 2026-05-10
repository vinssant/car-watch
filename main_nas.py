# =============================================================
# main_nas.py — Orchestrateur scrapers NAS (IP résidentielle)
# Scrapers : Le Parking + Autoscout24 NAS
# =============================================================

import sys
from datetime import datetime

from scrapers import leparking
from scrapers.autoscout24_nas import scraper as autoscout24_nas_scraper
from scrapers.gmail_parser import scraper as gmail_parser_scraper

from modeles import charger_modeles_actifs
from core.scorer       import calculer_score, trier_annonces
from core.deduplicator import traiter_annonces, charger_statistiques
from core.reporter     import generer_email_modele, generer_sujet_email
from core.mailer       import envoyer_email
from config            import EMAIL_DESTINATAIRE

SCRAPERS_NAS = {
    "leparking"       : leparking.scraper,
    "autoscout24_nas" : autoscout24_nas_scraper,
    "gmail_parser"    : gmail_parser_scraper,
}

# Sources NAS à activer dans chaque modèle
SOURCES_NAS_IDS = {"leparking", "autoscout24_nas", "autoscout24"}


def main():
    print(f"\n{'='*55}")
    print(f"  🏠 car-watch NAS — Scrapers IP résidentielle")
    print(f"  {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
    print(f"{'='*55}")

    modeles = charger_modeles_actifs()
    if not modeles:
        print("⚠️  Aucun modèle actif")
        sys.exit(1)

    for modele in modeles:
        print(f"\n{modele['emoji']} {modele['nom']}")
        annonces_brutes = []

        # Lancer tous les scrapers NAS disponibles
        for source_id, scraper_fn in SCRAPERS_NAS.items():
            nom = source_id.replace("_", " ").title()
            print(f"  🔍 {nom}...")
            try:
                resultats = scraper_fn(modele=modele)
                for a in resultats:
                    a.setdefault("source_id", source_id)
                    a.setdefault("fiabilite_source", 6)
                annonces_brutes.extend(resultats)
            except Exception as e:
                print(f"  ❌ {nom} — {e}")

        if not annonces_brutes:
            print(f"  ℹ️  Aucune annonce collectée depuis le NAS")
            continue

        # Scoring
        scorees = trier_annonces([calculer_score(a, modele) for a in annonces_brutes])

        # Déduplication avec suffixe _nas pour séparer de GitHub Actions
        resultats = traiter_annonces(scorees, modele["id"] + "_nas")
        stats     = charger_statistiques(modele["id"] + "_nas")

        s = resultats["stats"]
        print(f"  📋 Nouvelles: {s['nouvelles']} · Baisses: {s['baisses_prix']} · Total: {s['total_actives']}")

        # Email si nouveautés
        if resultats.get("nouvelles") or resultats.get("prix_baisses"):
            sujet = generer_sujet_email(modele, resultats)
            sujet = sujet.replace("🚗", "🏠🚗")  # marquer comme NAS
            corps = generer_email_modele(modele, resultats, stats)
            envoyer_email(EMAIL_DESTINATAIRE, sujet, corps)
            print(f"  📧 Email envoyé")
        else:
            print(f"  ℹ️  Pas de nouveautés — email non envoyé")

    print(f"\n✅ NAS terminé — {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
