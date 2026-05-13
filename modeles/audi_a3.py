# =============================================================
# modeles/audi_a3.py — Audi A3 Sportback
# Modèle 3 — Actif
# =============================================================

MODELE = {

    # ── Identité ─────────────────────────────────────────────
    "id"          : "audi_a3",
    "nom"         : "Audi A3 Sportback",
    "actif"       : True,
    "emoji"       : "🚘",
    "description" : "Audi A3 Sportback — toutes motorisations",

    # ── Critères véhicule ────────────────────────────────────
    "criteres": {
        "marque"           : "Audi",
        "modele"           : "A3",
        "version"          : "Sportback",
        "carrosserie"      : "berline compacte",
        "motorisation"     : "tous",
        "puissance_min_ch" : None,
        "annee_min"        : 2014,
        "annee_max"        : 2026,
        "km_max"           : 160000,
        "km_ideal_max"     : 100000,
        "budget_max"       : 10000,
        "budget_ideal_max" : 8000,
        "garantie_min_mois": 12,
        "vendeur_pro"      : True,
    },

    # ── Équipements clés ─────────────────────────────────────
    "equipements_cles": {
        "toit_ouvrant"          : {"poids": 0.7, "label": "Toit ouvrant"},
        "camera_360"            : {"poids": 0.15, "label": "Caméra"},
        "entretien_constructeur": {"poids": 0.15, "label": "Entretien Audi"},
    },

    # ── Cotes marché de référence ────────────────────────────
    "cotes_marche": [
        {"annee": 2020, "km_max": 80000,  "cote": 16000},
        {"annee": 2020, "km_max": 130000, "cote": 13000},
        {"annee": 2018, "km_max": 80000,  "cote": 12000},
        {"annee": 2018, "km_max": 130000, "cote": 9500},
        {"annee": 2016, "km_max": 100000, "cote": 9000},
        {"annee": 2016, "km_max": 160000, "cote": 7000},
        {"annee": 2014, "km_max": 100000, "cote": 7500},
        {"annee": 2014, "km_max": 160000, "cote": 5500},
    ],

    # ── Sources actives ──────────────────────────────────────
    "sources_actives": [
        {
            "id"       : "autoscout24",
            "nom"      : "Autoscout24",
            "url"      : "https://www.autoscout24.fr/lst/audi/a3/bt_estate",
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
            "url"      : "https://www.leparking.fr/voiture-occasion/audi-a3-sportback.html",
            "garantie" : "Variable selon vendeur",
            "actif"    : True,
        },
        {
            "id"       : "leboncoin",
            "nom"      : "Leboncoin",
            "url"      : "https://www.leboncoin.fr/ck/voitures/audi-a3",
            "garantie" : "Variable",
            "actif"    : True,
        },
        {
            "id"       : "autohero",
            "nom"      : "Autohero",
            "url"      : "https://www.autohero.com/fr/auto/audi/a3/",
            "garantie" : "12 mois inclus",
            "actif"    : True,
        },
        {
            "id"       : "aramisauto",
            "nom"      : "Aramisauto",
            "url"      : "https://www.aramisauto.com/voitures/audi/a3/",
            "garantie" : "12 mois + 0€ entretien",
            "actif"    : True,
        },
    ],

    # ── Annonces en suivi manuel ──────────────────────────────
    "annonces_suivies": [],

    # ── Surcharge scoring ─────────────────────────────────────
    "scoring_override": {},
}
