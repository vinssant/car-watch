# =============================================================
# core/deduplicator.py — Historique des annonces par modèle
# Chaque modèle a son propre dossier data/{modele_id}/
# =============================================================

import json
import hashlib
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def _dossier_modele(modele_id: str) -> Path:
    d = DATA_DIR / modele_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _charger(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [] if path.suffix == ".json" else {}


def _sauvegarder(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _id_annonce(annonce: dict) -> str:
    url = annonce.get("url", "")
    if url:
        return hashlib.md5(url.encode()).hexdigest()[:12]
    cle = f"{annonce.get('source','')}-{annonce.get('titre','')}-{annonce.get('prix','')}"
    return hashlib.md5(cle.encode()).hexdigest()[:12]


def traiter_annonces(annonces: list, modele_id: str) -> dict:
    """
    Traite les annonces d'un modèle spécifique.
    Détecte nouveautés, baisses de prix, disparitions.
    """
    dossier      = _dossier_modele(modele_id)
    seen_path    = dossier / "seen_ads.json"
    history_path = dossier / "ads_history.json"

    vues       = _charger(seen_path)
    historique = _charger(history_path)
    now        = datetime.now().isoformat()

    vues_index          = {a["id"]: a for a in vues if isinstance(a, dict) and "id" in a}
    nouvelles           = []
    prix_baisses        = []
    prix_hausses        = []
    inchangees          = []
    ids_vus_aujourd_hui = set()

    for annonce in annonces:
        ad_id = _id_annonce(annonce)
        annonce["id"]           = ad_id
        annonce["derniere_vue"] = now
        ids_vus_aujourd_hui.add(ad_id)

        if ad_id not in vues_index:
            annonce["premiere_vue"] = now
            annonce["est_nouvelle"] = True
            nouvelles.append(annonce)
            historique.append({"id": ad_id, "date": now, "event": "APPARITION",
                                "prix": annonce.get("prix"), "km": annonce.get("km"),
                                "titre": annonce.get("titre"), "source": annonce.get("source")})
        else:
            ancienne = vues_index[ad_id]
            annonce["premiere_vue"] = ancienne.get("premiere_vue", now)
            annonce["est_nouvelle"] = False

            ancien_prix  = ancienne.get("prix")
            nouveau_prix = annonce.get("prix")

            if ancien_prix and nouveau_prix and ancien_prix != nouveau_prix:
                diff     = nouveau_prix - ancien_prix
                diff_pct = round((diff / ancien_prix) * 100, 1)
                annonce.update({"prix_variation": diff, "prix_variation_pct": diff_pct,
                                "prix_precedent": ancien_prix})
                if diff < 0:
                    annonce["prix_baisse"] = True
                    prix_baisses.append(annonce)
                    historique.append({"id": ad_id, "date": now, "event": "BAISSE_PRIX",
                                       "ancien": ancien_prix, "nouveau": nouveau_prix, "diff_pct": diff_pct})
                else:
                    annonce["prix_hausse"] = True
                    prix_hausses.append(annonce)
            else:
                inchangees.append(annonce)

    # Disparitions
    disparues = []
    for ad_id, ancienne in vues_index.items():
        if ad_id not in ids_vus_aujourd_hui:
            ancienne["statut_disparition"] = now
            disparues.append(ancienne)
            historique.append({"id": ad_id, "date": now, "event": "DISPARITION",
                                "titre": ancienne.get("titre"), "prix": ancienne.get("prix")})

    toutes_actives = nouvelles + prix_baisses + prix_hausses + inchangees
    _sauvegarder(seen_path, toutes_actives)
    _sauvegarder(history_path, historique)

    return {
        "nouvelles"     : nouvelles,
        "prix_baisses"  : prix_baisses,
        "prix_hausses"  : prix_hausses,
        "disparues"     : disparues,
        "inchangees"    : inchangees,
        "toutes_actives": toutes_actives,
        "stats": {
            "total_actives": len(toutes_actives),
            "nouvelles"    : len(nouvelles),
            "baisses_prix" : len(prix_baisses),
            "disparues"    : len(disparues),
            "date_analyse" : now,
        }
    }


def charger_statistiques(modele_id: str) -> dict:
    dossier    = _dossier_modele(modele_id)
    actives    = _charger(dossier / "seen_ads.json")
    historique = _charger(dossier / "ads_history.json")

    if not actives:
        return {}

    prix_valides = [a["prix"] for a in actives if a.get("prix")]
    km_valides   = [a["km"]   for a in actives if a.get("km")]
    baisses      = [e for e in historique if e.get("event") == "BAISSE_PRIX"]
    disparitions = [e for e in historique if e.get("event") == "DISPARITION"]
    apparitions  = [e for e in historique if e.get("event") == "APPARITION"]

    durees = []
    app_idx = {e["id"]: e["date"] for e in apparitions}
    for d in disparitions:
        if d.get("id") in app_idx:
            try:
                t0 = datetime.fromisoformat(app_idx[d["id"]])
                t1 = datetime.fromisoformat(d["date"])
                durees.append((t1 - t0).days)
            except Exception:
                pass

    return {
        "total_actives"          : len(actives),
        "prix_moyen"             : round(sum(prix_valides) / len(prix_valides)) if prix_valides else None,
        "prix_min"               : min(prix_valides) if prix_valides else None,
        "prix_max"               : max(prix_valides) if prix_valides else None,
        "km_moyen"               : round(sum(km_valides) / len(km_valides)) if km_valides else None,
        "total_baisses_prix"     : len(baisses),
        "total_vues_historique"  : len(set(e.get("id") for e in historique)),
        "duree_moy_marche_jours" : round(sum(durees) / len(durees), 1) if durees else None,
    }


def stats_semaine(modele_id: str) -> dict:
    """Stats pour le digest hebdomadaire (7 derniers jours)."""
    from datetime import timedelta
    dossier    = _dossier_modele(modele_id)
    historique = _charger(dossier / "ads_history.json")
    seuil      = (datetime.now() - timedelta(days=7)).isoformat()

    recents    = [e for e in historique if e.get("date", "") >= seuil]
    return {
        "nouvelles_semaine" : sum(1 for e in recents if e.get("event") == "APPARITION"),
        "disparues_semaine" : sum(1 for e in recents if e.get("event") == "DISPARITION"),
        "baisses_semaine"   : sum(1 for e in recents if e.get("event") == "BAISSE_PRIX"),
    }
