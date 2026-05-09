# =============================================================
# core/scorer.py — Moteur de scoring TCO générique
# Fonctionne avec n'importe quel modèle de modeles/
# =============================================================

from datetime import datetime
from config import SCORING_DEFAULT, SCORE_URGENT, SCORE_ALERTE, SCORE_INFO


def _get_cote(modele: dict, annee: int, km: int) -> float | None:
    """Retourne la cote de référence selon l'année et le km."""
    cotes = modele.get("cotes_marche", [])
    # Filtrer par année, puis prendre le premier km_max >= km actuel
    candidats = [c for c in cotes if c.get("annee") == annee and c.get("km_max", 0) >= (km or 0)]
    if candidats:
        return min(candidats, key=lambda c: c["km_max"])["cote"]
    # Fallback : année la plus proche
    par_annee = sorted(cotes, key=lambda c: abs(c.get("annee", 0) - (annee or 0)))
    return par_annee[0]["cote"] if par_annee else None


def score_annee(annee: int, annee_min: int) -> float:
    if annee is None:
        return 0
    delta = annee - annee_min
    if delta >= 2:
        return 1.0
    if delta == 1:
        return 0.85
    if delta == 0:
        return 0.70
    return 0.30


def score_kilometrage(km: int, km_ideal_max: int, km_max: int) -> float:
    if km is None:
        return 0
    if km <= km_ideal_max * 0.4:
        return 1.0
    if km <= km_ideal_max * 0.6:
        return 0.90
    if km <= km_ideal_max:
        return 0.75
    if km <= km_max * 0.75:
        return 0.50
    if km <= km_max:
        return 0.25
    return 0.0


def score_prix(prix: float, cote: float | None) -> float:
    if prix is None or cote is None:
        return 0.5
    ratio = prix / cote
    if ratio <= 0.88:
        return 1.0
    if ratio <= 0.93:
        return 0.85
    if ratio <= 0.98:
        return 0.70
    if ratio <= 1.03:
        return 0.50
    if ratio <= 1.08:
        return 0.30
    return 0.10


def score_garantie(mois: int, garantie_min: int) -> float:
    if mois is None:
        return 0
    if mois >= 24:
        return 1.0
    if mois >= garantie_min:
        return 0.75
    if mois >= garantie_min // 2:
        return 0.40
    return 0.10


def score_equipements(annonce: dict, equipements_cles: dict) -> float:
    """Score les équipements clés définis dans le modèle."""
    if not equipements_cles:
        return 0.5
    total_poids  = sum(e["poids"] for e in equipements_cles.values())
    poids_obtenus = 0.0
    for cle, meta in equipements_cles.items():
        val = annonce.get(cle) or annonce.get("equipements", {}).get(cle)
        if val is True:
            poids_obtenus += meta["poids"]
        elif val is None:
            poids_obtenus += meta["poids"] * 0.3  # inconnu → malus partiel
    return min(poids_obtenus / total_poids, 1.0) if total_poids > 0 else 0.5


def score_source(fiabilite: int) -> float:
    return min(fiabilite / 10, 1.0)


def calculer_score(annonce: dict, modele: dict) -> dict:
    """
    Calcule le score TCO d'une annonce pour un modèle donné.
    Retourne l'annonce enrichie avec score_total, score_detail,
    niveau_alerte, recommandation.
    """
    criteres = modele.get("criteres", {})
    scoring  = {**SCORING_DEFAULT, **modele.get("scoring_override", {})}
    equip_cles = modele.get("equipements_cles", {})

    annee      = annonce.get("annee")
    km         = annonce.get("km")
    prix       = annonce.get("prix")
    garantie   = annonce.get("garantie_mois")
    fiabilite  = annonce.get("fiabilite_source", 5)

    cote = _get_cote(modele, annee, km)

    details = {
        "annee"           : score_annee(annee, criteres.get("annee_min", 2023)),
        "kilometrage"     : score_kilometrage(km,
                                criteres.get("km_ideal_max", 50000),
                                criteres.get("km_max", 65000)),
        "prix_vs_marche"  : score_prix(prix, cote),
        "garantie"        : score_garantie(garantie, criteres.get("garantie_min_mois", 12)),
        "equipements_cles": score_equipements(annonce, equip_cles),
        "fiabilite_source": score_source(fiabilite),
    }

    total = sum(details[k] * scoring.get(k, 0) for k in details)

    # Niveau d'alerte
    if total >= SCORE_URGENT:
        niveau, emoji = "URGENT", "🔴"
    elif total >= SCORE_ALERTE:
        niveau, emoji = "ALERTE", "🟠"
    elif total >= SCORE_INFO:
        niveau, emoji = "INFO", "🟡"
    else:
        niveau, emoji = "FAIBLE", "⚪"

    return {
        **annonce,
        "modele_id"     : modele["id"],
        "modele_nom"    : modele["nom"],
        "score_total"   : round(total, 1),
        "score_detail"  : {k: round(v * 100, 1) for k, v in details.items()},
        "cote_reference": cote,
        "niveau_alerte" : niveau,
        "emoji_alerte"  : emoji,
        "recommandation": _recommandation(annonce, details, modele),
        "score_date"    : datetime.now().isoformat(),
    }


def _recommandation(annonce: dict, details: dict, modele: dict) -> str:
    equip_cles = modele.get("equipements_cles", {})
    points = []

    if details["kilometrage"] >= 0.9:
        points.append(f"✅ Kilométrage excellent ({annonce.get('km', '?')} km)")
    if details["prix_vs_marche"] >= 0.85:
        points.append("✅ Prix sous la cote — opportunité")
    if details["garantie"] >= 0.75:
        points.append(f"✅ Garantie solide ({annonce.get('garantie_mois', '?')} mois)")

    for cle, meta in equip_cles.items():
        val = annonce.get(cle) or annonce.get("equipements", {}).get(cle)
        if val is True:
            points.append(f"✅ {meta['label']} confirmé")
        elif val is None and meta.get("poids", 0) >= 0.4:
            points.append(f"⚠️ {meta['label']} : à confirmer avant visite")
        elif val is False and meta.get("poids", 0) >= 0.4:
            points.append(f"⛔ {meta['label']} absent")

    if details["kilometrage"] < 0.4:
        points.append(f"⚠️ Kilométrage élevé ({annonce.get('km', '?')} km)")
    if details["prix_vs_marche"] < 0.4:
        points.append("⚠️ Prix surévalué — négocier")
    if details["garantie"] < 0.4:
        points.append("⚠️ Garantie insuffisante — exiger extension 12 mois")

    return " · ".join(points) if points else "Annonce standard — vérifier les détails"


def trier_annonces(annonces: list) -> list:
    return sorted(annonces, key=lambda a: a.get("score_total", 0), reverse=True)
