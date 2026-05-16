# =============================================================
# modeles/mercedes_a.py — Mercedes Classe A
# Modèle 4 — Actif
# =============================================================

MODELE = {

    # ── Identité ─────────────────────────────────────────────
    "id"          : "mercedes_a",
    "nom"         : "Mercedes Classe A",
    "actif"       : True,
    "emoji"       : "🚖",
    "description" : "Mercedes Classe A — toutes carrosseries",

    # ── Critères véhicule ────────────────────────────────────
    "criteres": {
        "marque"           : "Mercedes-Benz",
        "modele"           : "Classe A",
        "version"          : None,
        "carrosserie"      : "tous",
        "motorisation"     : "tous",
        "puissance_min_ch" : None,
        "annee_min"        : 2016,
        "annee_max"        : 2026,
        "km_max"           : 160000,
        "km_ideal_max"     : 100000,
        "budget_max"       : 12000,
        "budget_ideal_max" : 10000,
        "garantie_min_mois": 12,
        "vendeur_pro"      : True,
    },

    # ── Équipements clés ─────────────────────────────────────
    "equipements_cles": {
        "toit_ouvrant"          : {"poids": 0.6, "label": "Toit ouvrant"},
        "camera_360"            : {"poids": 0.2, "label": "Caméra"},
        "entretien_constructeur": {"poids": 0.2, "label": "Entretien MB"},
    },

    # ── Cotes marché de référence ────────────────────────────
    "cotes_marche": [
        {"annee": 2021, "km_max": 80000,  "cote": 18000},
        {"annee": 2021, "km_max": 130000, "cote": 14000},
        {"annee": 2019, "km_max": 80000,  "cote": 14000},
        {"annee": 2019, "km_max": 130000, "cote": 11000},
        {"annee": 2018, "km_max": 80000,  "cote": 12000},
        {"annee": 2018, "km_max": 130000, "cote": 9500},
        {"annee": 2016, "km_max": 100000, "cote": 10000},
        {"annee": 2016, "km_max": 160000, "cote": 7500},
    ],

    # ── Sources actives ──────────────────────────────────────
    "sources_actives": [
        {
            "id"       : "autoscout24",
            "nom"      : "Autoscout24",
            "url"      : "https://www.autoscout24.fr/lst/mercedes-benz/a-klasse",
            "garantie" : "Variable",
            "actif"    : True,
        },
        {
            "id"       : "lacentrale",
            "nom"      : "La Centrale",
            "url"      : "https://www.lacentrale.fr/",
            "garantie" : "Variable",
            "actif"    : True,
        },
        {
            "id"       : "leparking",
            "nom"      : "Le Parking",
            "url"      : "https://www.leparking.fr/voiture-occasion/mercedes-classe-a.html",
            "garantie" : "Variable selon vendeur",
            "actif"    : True,
        },
        {
            "id"       : "leboncoin",
            "nom"      : "Leboncoin",
            "url"      : "https://www.leboncoin.fr/ck/voitures/mercedes-classe-a",
            "garantie" : "Variable",
            "actif"    : True,
        },
        {
            "id"       : "aramisauto",
            "nom"      : "Aramisauto",
            "url"      : "https://www.aramisauto.com/voitures/mercedes/classe-a/",
            "garantie" : "12 mois + 0€ entretien",
            "actif"    : True,
        },
    ],

    # ── Annonces en suivi manuel ──────────────────────────────
    "annonces_suivies": [],

    # ── Surcharge scoring ─────────────────────────────────────
    "scoring_override": {},
}
