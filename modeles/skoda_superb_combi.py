# =============================================================
# modeles/skoda_superb_combi.py — Skoda Superb IV Combi PHEV
# Modèle 3 — Inactif (mettre actif: True pour surveiller)
# =============================================================

MODELE = {

    # ── Identité ─────────────────────────────────────────────
    "id"          : "skoda_superb_combi",
    "nom"         : "Skoda Superb Combi PHEV",
    "actif"       : False,   # ← passer à True pour activer
    "emoji"       : "🥈",
    "description" : "Skoda Superb IV Combi 1.5 TSI 204ch PHEV — Meilleur espace/TCO",

    # ── Critères véhicule ────────────────────────────────────
    "criteres": {
        "marque"           : "Skoda",
        "modele"           : "Superb",
        "version"          : "Combi",
        "carrosserie"      : "break",
        "motorisation"     : "PHEV",
        "puissance_min_ch" : 200,
        "annee_min"        : 2024,          # Superb IV = 2024+
        "annee_max"        : 2026,
        "km_max"           : 50000,
        "km_ideal_max"     : 25000,
        "budget_max"       : 42000,
        "budget_ideal_max" : 40000,
        "garantie_min_mois": 12,
    },

    # ── Équipements clés ─────────────────────────────────────
    "equipements_cles": {
        "toit_ouvrant"          : {"poids": 0.4, "label": "Toit ouvrant"},
        "camera_360"            : {"poids": 0.3, "label": "Caméra 360°"},
        "entretien_constructeur": {"poids": 0.3, "label": "Entretien Skoda"},
    },

    # ── Cotes marché de référence ────────────────────────────
    "cotes_marche": [
        {"annee": 2025, "km_max": 10000,  "cote": 44000},
        {"annee": 2025, "km_max": 30000,  "cote": 41000},
        {"annee": 2024, "km_max": 20000,  "cote": 42000},
        {"annee": 2024, "km_max": 40000,  "cote": 38000},
    ],

    # ── Sources actives ──────────────────────────────────────
    "sources_actives": [
        {
            "id"   : "autohero",
            "nom"  : "Autohero",
            "url"  : "https://www.autohero.com/fr/auto/skoda/superb/",
            "actif": True,
        },
        {
            "id"   : "aramisauto",
            "nom"  : "Aramisauto",
            "url"  : "https://www.aramisauto.com/voitures/skoda/superb/offres/hybride-rechargeable/",
            "actif": True,
        },
        {
            "id"   : "spoticar",
            "nom"  : "Spoticar",
            "url"  : "https://www.spoticar.fr/voitures-occasion/skoda/superb",
            "actif": True,
        },
        {
            "id"   : "autoscout24",
            "nom"  : "Autoscout24",
            "url"  : "https://www.autoscout24.fr/lst/skoda/superb/bt_estate/re_2024",
            "actif": True,
        },
        {
            "id"   : "leboncoin",
            "nom"  : "Leboncoin",
            "url"  : "https://www.leboncoin.fr/ck/voitures/skoda-superb-combi",
            "actif": True,
        },
        {
            "id"   : "lacentrale",
            "nom"  : "La Centrale",
            "url"  : "https://www.lacentrale.fr/",
            "actif": True,
        },
    ],

    # ── Annonces en suivi manuel ──────────────────────────────
    "annonces_suivies": [
        {
            "id"      : "villemomble_superb_2025_100km",
            "titre"   : "Superb Combi PHEV Selection 2025 · 100 km",
            "vendeur" : "Pro — Villemomble (93)",
            "prix"    : 38980,
            "url"     : "https://www.leboncoin.fr/",
            "annee"   : 2025,
            "km"      : 100,
            "equipements": {"toit_ouvrant": None},
            "garantie_mois": None,
            "statut"  : "A_VERIFIER",
            "notes"   : "Pratiquement neuve. Vérifier garantie et toit ouvrant.",
            "date_ajout": "2026-05-08",
        },
    ],

    # ── Surcharge scoring ────────────────────────────────────
    "scoring_override": {},
}
