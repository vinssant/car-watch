# =============================================================
# main.py — Orchestrateur car-watch (multi-modèles)
# Usage :
#   python3 main.py              → veille quotidienne tous modèles actifs
#   python3 main.py --test       → test sans envoi email
#   python3 main.py --digest     → génère le digest hebdomadaire
#   python3 main.py --modele mercedes_c300e  → un seul modèle
# =============================================================

import sys
import traceback
from datetime import datetime

from config import EMAIL_DESTINATAIRE
from modeles import charger_modeles_actifs, charger_tous_modeles
from core.scorer       import calculer_score, trier_annonces
from core.deduplicator import traiter_annonces, charger_statistiques, stats_semaine
from core.reporter     import (generer_email_modele, generer_sujet_email,
                                generer_digest_hebdo, generer_sujet_digest)
from core.mailer       import envoyer_email

# Import scrapers génériques
from scrapers import autohero, aramisauto, autoscout24
from scrapers import spoticar, mercedes_certified, elite_auto, lacentrale, capcar


# ── Mapping scraper → fonction ────────────────────────────────
SCRAPERS_DISPONIBLES = {
    "autohero"          : autohero.scraper,
    "aramisauto"        : aramisauto.scraper,
    "autoscout24"       : autoscout24.scraper,
    "spoticar"          : spoticar.scraper,
    "mercedes_certified": mercedes_certified.scraper,
    "elite_auto"        : elite_auto.scraper,
    "lacentrale"        : lacentrale.scraper,
    "capcar"            : capcar.scraper,
    # À décommenter au fur et à mesure :
}


def scraper_pour_modele(modele: dict) -> list:
    """Lance les scrapers actifs pour un modèle donné."""
    annonces = []
    sources_actives = [s for s in modele.get("sources_actives", []) if s.get("actif")]

    for source in sources_actives:
        source_id = source["id"]
        if source_id not in SCRAPERS_DISPONIBLES:
            continue  # scraper pas encore codé → on skippe silencieusement
        print(f"    🔍 {source['nom']}...")
        try:
            # Passer le modèle au scraper pour filtrer à la source
            resultats = SCRAPERS_DISPONIBLES[source_id](modele=modele)
            # Annoter avec la source
            for a in resultats:
                a["source"]           = source["nom"]
                a["source_id"]        = source_id
                a["fiabilite_source"] = source.get("fiabilite_source",
                                        _fiabilite(source_id))
            annonces.extend(resultats)
        except TypeError:
            # Scraper ancienne version sans param modele
            try:
                resultats = SCRAPERS_DISPONIBLES[source_id]()
                for a in resultats:
                    a.setdefault("source", source["nom"])
                    a.setdefault("source_id", source_id)
                    a.setdefault("fiabilite_source", _fiabilite(source_id))
                annonces.extend(resultats)
            except Exception as e:
                print(f"    ❌ {source['nom']} — {e}")
        except Exception as e:
            print(f"    ❌ {source['nom']} — {e}")
            traceback.print_exc()

    return annonces


def _fiabilite(source_id: str) -> int:
    from config import SOURCES_FIABILITE
    return SOURCES_FIABILITE.get(source_id, 5)


def traiter_modele(modele: dict, mode_test: bool = False) -> dict | None:
    """Pipeline complet pour un modèle : scrape → score → déduplique → email."""
    print(f"\n{'─'*50}")
    print(f"  {modele['emoji']} {modele['nom']}")
    print(f"{'─'*50}")

    # 1. Scraping
    annonces_brutes = scraper_pour_modele(modele)
    print(f"  📦 {len(annonces_brutes)} annonces collectées")

    # 2. Scoring
    scorees = [calculer_score(a, modele) for a in annonces_brutes]
    scorees = trier_annonces(scorees)

    # 3. Déduplication
    resultats = traiter_annonces(scorees, modele["id"])
    stats_m   = charger_statistiques(modele["id"])
    s         = resultats["stats"]
    print(f"  📋 Nouvelles: {s['nouvelles']} · Baisses: {s['baisses_prix']} · Disparues: {s['disparues']}")

    if mode_test:
        print(f"\n  🏆 Top 3 :")
        for i, a in enumerate(scorees[:3], 1):
            print(f"    #{i} [{a['score_total']}/100] {a['titre']} — {a.get('prix','?')}€")
        return {"modele": modele, "resultats": resultats, "stats": stats_m}

    # 4. Email quotidien
    sujet = generer_sujet_email(modele, resultats)
    corps = generer_email_modele(modele, resultats, stats_m)
    envoyer_email(EMAIL_DESTINATAIRE, sujet, corps)

    return {"modele": modele, "resultats": resultats, "stats": stats_m}


def run_digest():
    """Génère et envoie le digest hebdomadaire."""
    print("\n📊 Génération du digest hebdomadaire...")
    tous_modeles = charger_modeles_actifs()
    items        = []

    for modele in tous_modeles:
        resultats = traiter_annonces([], modele["id"])  # résultats courants sans nouveau scraping
        stats_m   = charger_statistiques(modele["id"])
        sem       = stats_semaine(modele["id"])
        items.append({
            "modele"          : modele,
            "resultats"       : {"toutes_actives": []},
            "stats"           : stats_m,
            **sem
        })

    corps = generer_digest_hebdo(items)
    sujet = generer_sujet_digest()
    envoyer_email(EMAIL_DESTINATAIRE, sujet, corps)
    print("✅ Digest envoyé")


def main():
    args       = sys.argv[1:]
    mode_test  = "--test"   in args
    mode_digest= "--digest" in args
    filtre     = next((args[i+1] for i, a in enumerate(args) if a == "--modele" and i+1 < len(args)), None)

    print(f"\n{'='*55}")
    print(f"  🚗 car-watch — {'TEST' if mode_test else 'DIGEST' if mode_digest else 'Veille'}")
    print(f"  {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
    print(f"{'='*55}")

    if mode_digest:
        run_digest()
        return

    modeles = charger_modeles_actifs()
    if not modeles:
        print("⚠️  Aucun modèle actif — vérifiez modeles/*.py (actif: True)")
        sys.exit(1)

    if filtre:
        modeles = [m for m in modeles if m["id"] == filtre]
        if not modeles:
            print(f"❌ Modèle '{filtre}' non trouvé ou inactif")
            sys.exit(1)

    print(f"\n📋 {len(modeles)} modèle(s) actif(s) :")
    for m in modeles:
        print(f"  {m['emoji']} {m['nom']}")

    for modele in modeles:
        traiter_modele(modele, mode_test=mode_test)

    print(f"\n✅ car-watch terminé — {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
