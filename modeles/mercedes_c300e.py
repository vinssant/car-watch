# =============================================================
# modeles/mercedes_c300e.py — Mercedes Classe C 300e Break
# Modèle 1 — Actif
# =============================================================
# Pour activer/désactiver ce modèle : changer "actif": True/False
# Pour modifier les critères : éditer ce fichier uniquement
# =============================================================

MODELE = {

    # ── Identité ─────────────────────────────────────────────
    "id"          : "mercedes_c300e",
    "nom"         : "Mercedes C300e Break",
    "actif"       : True,
    "emoji"       : "🚗",
    "description" : "Mercedes Classe C 300e T-Modell Break PHEV 313ch",

    # ── Critères véhicule ────────────────────────────────────
    "criteres": {
        "marque"           : "Mercedes-Benz",
        "modele"           : "Classe C",
        "version"          : "300e",
        "carrosserie"      : "break",       # T-Modell uniquement, pas berline
        "motorisation"     : "PHEV",
        "puissance_min_ch" : 300,           # 313 ch combinés
        "annee_min"        : 2023,
        "annee_max"        : 2026,
        "km_max"           : 65000,         # seuil absolu
        "km_ideal_max"     : 50000,         # bonus scoring
        "budget_max"       : 42000,         # € TTC seuil absolu
        "budget_ideal_max" : 40000,         # € TTC bonus scoring
        "garantie_min_mois": 12,
    },

    # ── Équipements clés (critère "equipements_cles" du scoring)
    # Chaque équipement présent ajoute du poids au score
    "equipements_cles": {
        "toit_ouvrant"          : {"poids": 0.6, "label": "Toit ouvrant"},     # critique
        "camera_360"            : {"poids": 0.2, "label": "Caméra 360°"},
        "entretien_constructeur": {"poids": 0.2, "label": "Entretien MB"},
    },

    # ── Cotes marché de référence (pour scoring prix_vs_marche)
    # Format : (annee, km_max) → prix_reference_€
    "cotes_marche": [
        {"annee": 2024, "km_max": 20000,  "cote": 46000},
        {"annee": 2024, "km_max": 50000,  "cote": 42000},
        {"annee": 2023, "km_max": 30000,  "cote": 42000},
        {"annee": 2023, "km_max": 50000,  "cote": 38000},
        {"annee": 2023, "km_max": 65000,  "cote": 34000},
        {"annee": 2022, "km_max": 50000,  "cote": 35000},
        {"annee": 2022, "km_max": 65000,  "cote": 30000},
    ],

    # ── Sources actives pour ce modèle ───────────────────────
    # Seules les sources ayant des C300e break en stock
    "sources_actives": [
        {
            "id"       : "autohero",
            "nom"      : "Autohero",
            "url"      : "https://www.autohero.com/fr/auto/mercedes-benz/c-klasse/",
            "garantie" : "12 mois inclus",
            "actif"    : True,
        },
        {
            "id"       : "aramisauto",
            "nom"      : "Aramisauto",
            "url"      : "https://www.aramisauto.com/voitures/mercedes/classe-c-break/offres/hybride-rechargeable/",
            "garantie" : "12 mois + 0€ entretien",
            "actif"    : True,
        },
        {
            "id"       : "spoticar",
            "nom"      : "Spoticar",
            "url"      : "https://www.spoticar.fr/voitures-occasion/mercedes/classe-c",
            "garantie" : "12-24 mois illimité",
            "actif"    : True,
        },
        {
            "id"       : "mercedes_certified",
            "nom"      : "Mercedes-Benz Certified",
            "url"      : "https://www.mercedes-benz.fr/passengercars/buy/used-cars.html",
            "garantie" : "12-24 mois constructeur",
            "actif"    : True,
        },
        {
            "id"       : "transakauto",
            "nom"      : "Transakauto",
            "url"      : "https://annonces.transakauto.com/",
            "garantie" : "12 mois",
            "actif"    : True,
        },
        {
            "id"       : "elite_auto",
            "nom"      : "Elite-Auto",
            "url"      : "https://www.elite-auto.fr/occasion/hybride/marque-mercedes",
            "garantie" : "12 mois",
            "actif"    : True,
        },
        {
            "id"       : "jean_lain",
            "nom"      : "Jean Lain Occasions",
            "url"      : "https://www.jeanlain-occasions.com/",
            "garantie" : "12 mois extensible 5 ans",
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
            "id"       : "autoscout24",
            "nom"      : "Autoscout24",
            "url"      : "https://www.autoscout24.fr/lst/mercedes-benz/c-300/bt_estate/re_2023",
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
            "id"       : "ewigo",
            "nom"      : "Ewigo",
            "url"      : "https://www.ewigo.com/",
            "garantie" : "6 mois min",
            "actif"    : True,
        },
        {
            "id"       : "simplicicar",
            "nom"      : "Simplicicar",
            "url"      : "https://www.simplicicar.com/voitures-occasion/mercedes/classe-c",
            "garantie" : "Variable",
            "actif"    : True,
        },
        {
            "id"       : "leboncoin",
            "nom"      : "Leboncoin",
            "url"      : "https://www.leboncoin.fr/ck/voitures/mercedes-classe-c-300e",
            "garantie" : "Variable",
            "actif"    : True,
        },
    ],

    # ── Annonces en suivi manuel ──────────────────────────────
    # Mettre à jour au fil de vos contacts vendeurs
    "annonces_suivies": [
        {
            "id"      : "ewigo_palaiseau_2023_24100",
            "titre"   : "C300e Break AMG Line 2023 · 24 100 km",
            "vendeur" : "Ewigo Palaiseau (91)",
            "prix"    : 39990,
            "url"     : "https://www.leboncoin.fr/ad/voitures/3092724405",
            "annee"   : 2023,
            "km"      : 24100,
            "equipements": {"toit_ouvrant": None, "camera_360": None},
            "garantie_mois": 6,
            "statut"  : "A_CONTACTER",
            "notes"   : "Toit ouvrant à confirmer. Négocier extension garantie 12 mois.",
            "date_ajout": "2026-05-08",
        },
        
    ],

    # ── Surcharge scoring (optionnel) ─────────────────────────
    # Laissez vide {} pour utiliser SCORING_DEFAULT de config.py
    "scoring_override": {},
}
