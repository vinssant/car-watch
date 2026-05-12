# =============================================================
# modeles/bmw_330e.py — BMW Série 3 330e Touring
# Modèle 2 — Actif
# =============================================================

MODELE = {

    # ── Identité ─────────────────────────────────────────────
    "id"          : "bmw_3series",
    "nom"         : "BMW Série 3 PHEV Touring",
    "actif"       : True,
    "emoji"       : "🚙",
    "description" : "BMW Série 3 Touring PHEV (320e / 330e) — G21",

    # ── Critères véhicule ────────────────────────────────────
    "criteres": {
        "marque"           : "BMW",
        "modele"           : "Série 3",
        "version"          : "320e/330e",
        "carrosserie"      : "break",
        "motorisation"     : "PHEV",
        "puissance_min_ch" : 200,
        "annee_min"        : 2023,
        "annee_max"        : 2026,
        "km_max"           : 60000,
        "km_ideal_max"     : 50000,
        "budget_max"       : 42000,
        "budget_ideal_max" : 40000,
        "garantie_min_mois": 12,
    },

    # ── Équipements clés ─────────────────────────────────────
    "equipements_cles": {
        "toit_ouvrant"          : {"poids": 0.6, "label": "Toit ouvrant / panoramique"},
        "camera_360"            : {"poids": 0.2, "label": "Caméra 360°"},
        "entretien_constructeur": {"poids": 0.2, "label": "Entretien BMW"},
    },

    # ── Cotes marché de référence ────────────────────────────
    "cotes_marche": [
        {"annee": 2024, "km_max": 20000,  "cote": 45000},
        {"annee": 2024, "km_max": 50000,  "cote": 41000},
        {"annee": 2023, "km_max": 30000,  "cote": 41000},
        {"annee": 2023, "km_max": 50000,  "cote": 37000},
        {"annee": 2023, "km_max": 65000,  "cote": 33000},
    ],

    # ── Sources actives ──────────────────────────────────────
    "sources_actives": [
        {
            "id"       : "autohero",
            "nom"      : "Autohero",
            "url"      : "https://www.autohero.com/fr/auto/bmw/3-series/",
            "garantie" : "12 mois inclus",
            "actif"    : True,
        },
        {
            "id"       : "aramisauto",
            "nom"      : "Aramisauto",
            "url"      : "https://www.aramisauto.com/voitures/bmw/serie-3-touring/offres/hybride-rechargeable/",
            "garantie" : "12 mois + 0€ entretien",
            "actif"    : True,
        },
        {
            "id"       : "autoscout24",
            "nom"      : "Autoscout24",
            "url"      : "https://www.autoscout24.fr/lst/bmw/330e/bt_estate/re_2023",
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
            "url"      : "https://www.leparking.fr/voiture-occasion/bmw-serie-3-touring-330e.html",
            "garantie" : "Variable selon vendeur",
            "actif"    : True,
        },
        {
            "id"       : "leboncoin",
            "nom"      : "Leboncoin",
            "url"      : "https://www.leboncoin.fr/ck/voitures/bmw-serie-3-330e",
            "garantie" : "Variable",
            "actif"    : True,
        },
        {
            "id"       : "capcar",
            "nom"      : "CapCar",
            "url"      : "https://www.capcar.fr/voiture-occasion",
            "garantie" : "6 mois + extension",
            "actif"    : True,
        },
        {
            "id"       : "elite_auto",
            "nom"      : "Elite-Auto",
            "url"      : "https://www.elite-auto.fr/occasion/hybride/marque-bmw",
            "garantie" : "12 mois",
            "actif"    : True,
        },
    ],

    # ── Annonces en suivi manuel ──────────────────────────────
    "annonces_suivies": [],

    # ── Surcharge scoring ─────────────────────────────────────
    "scoring_override": {},
}
