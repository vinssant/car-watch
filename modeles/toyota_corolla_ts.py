# =============================================================
# modeles/toyota_corolla_ts.py — Toyota Corolla Touring Sports
# Modèle 2 — Inactif (mettre actif: True pour surveiller)
# =============================================================

MODELE = {

    # ── Identité ─────────────────────────────────────────────
    "id"          : "toyota_corolla_ts",
    "nom"         : "Toyota Corolla Touring Sports",
    "actif"       : False,   # ← passer à True pour activer
    "emoji"       : "🏆",
    "description" : "Toyota Corolla Touring Sports 2.0 HEV 196ch — Meilleur TCO",

    # ── Critères véhicule ────────────────────────────────────
    "criteres": {
        "marque"           : "Toyota",
        "modele"           : "Corolla",
        "version"          : "Touring Sports",
        "carrosserie"      : "break",
        "motorisation"     : "HEV",          # hybride non rechargeable
        "puissance_min_ch" : 190,
        "annee_min"        : 2023,
        "annee_max"        : 2026,
        "km_max"           : 60000,
        "km_ideal_max"     : 40000,
        "budget_max"       : 38000,
        "budget_ideal_max" : 36000,
        "garantie_min_mois": 12,
    },

    # ── Équipements clés ─────────────────────────────────────
    "equipements_cles": {
        "toit_ouvrant"          : {"poids": 0.3, "label": "Toit ouvrant"},
        "camera_360"            : {"poids": 0.2, "label": "Caméra 360°"},
        "hud"                   : {"poids": 0.2, "label": "HUD"},
        "entretien_constructeur": {"poids": 0.3, "label": "Entretien Toyota"},
    },

    # ── Cotes marché de référence ────────────────────────────
    "cotes_marche": [
        {"annee": 2025, "km_max": 20000,  "cote": 38000},
        {"annee": 2024, "km_max": 20000,  "cote": 36000},
        {"annee": 2024, "km_max": 40000,  "cote": 34000},
        {"annee": 2023, "km_max": 30000,  "cote": 34000},
        {"annee": 2023, "km_max": 50000,  "cote": 31000},
    ],

    # ── Sources actives ──────────────────────────────────────
    "sources_actives": [
        {
            "id"   : "autohero",
            "nom"  : "Autohero",
            "url"  : "https://www.autohero.com/fr/auto/toyota/corolla/",
            "actif": True,
        },
        {
            "id"   : "aramisauto",
            "nom"  : "Aramisauto",
            "url"  : "https://www.aramisauto.com/voitures/toyota/corolla/offres/hybride/",
            "actif": True,
        },
        {
            "id"   : "autoscout24",
            "nom"  : "Autoscout24",
            "url"  : "https://www.autoscout24.fr/lst/toyota/corolla/bt_estate/re_2023",
            "actif": True,
        },
        {
            "id"   : "leboncoin",
            "nom"  : "Leboncoin",
            "url"  : "https://www.leboncoin.fr/ck/voitures/toyota-corolla-touring-sports",
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
            "id"      : "suzuki_tours_corolla_collection_2024",
            "titre"   : "Corolla TS 196ch Collection MY24 · 33 500 km",
            "vendeur" : "Suzuki Tours — Saint-Cyr-sur-Loire (37)",
            "prix"    : 33299,
            "url"     : "https://www.toyota.fr/",
            "annee"   : 2024,
            "km"      : 33500,
            "equipements": {"toit_ouvrant": None},
            "garantie_mois": 12,
            "statut"  : "A_CONTACTER",
            "notes"   : "Vérifier historique entretien des 33 500 km. Prix très compétitif.",
            "date_ajout": "2026-05-08",
        },
    ],

    # ── Surcharge scoring ────────────────────────────────────
    # Toyota : fiabilité prime encore plus sur le prix
    "scoring_override": {
        "kilometrage"     : 30,   # +5 vs défaut (fiabilité Toyota = km importants)
        "annee"           : 20,
        "prix_vs_marche"  : 15,   # -5 vs défaut
        "garantie"        : 15,
        "equipements_cles": 10,
        "fiabilite_source": 10,
    },
}
