# =============================================================
# config.py — Configuration globale car-watch
# Paramètres PARTAGÉS entre tous les modèles surveillés
# Pour les critères d'un modèle spécifique → voir modeles/
# =============================================================

# ── Identité ──────────────────────────────────────────────────
PROJET_NOM         = "car-watch"
PROJET_VERSION     = "1.0.0"
EMAIL_DESTINATAIRE = "vinssant@gmail.com"

# ── Scoring — pondérations globales (total = 100) ─────────────
# Ces poids s'appliquent à TOUS les modèles
# Chaque modèle peut les surcharger dans son fichier
SCORING_DEFAULT = {
    "kilometrage"     : 25,   # < km_ideal = max
    "annee"           : 20,   # annee récente = max
    "prix_vs_marche"  : 20,   # sous la cote = max
    "garantie"        : 15,   # ≥ 24 mois = max
    "equipements_cles": 10,   # critères spécifiques au modèle
    "fiabilite_source": 10,   # réseau officiel = max
}

# Seuils d'alerte (communs à tous les modèles)
SCORE_URGENT = 85   # 🔴 sujet email URGENT
SCORE_ALERTE = 70   # 🟠 prioritaire
SCORE_INFO   = 50   # 🟡 standard
SCORE_MIN    = 40   # ⚪ en dessous = ignoré

# ── Envoi email ───────────────────────────────────────────────
# Email quotidien : un par modèle actif
# Digest hebdomadaire : tous les modèles groupés (lundi matin)
ENVOI_QUOTIDIEN_HEURE = "08:00"   # heure Paris
DIGEST_HEBDO_JOUR     = "lundi"
DIGEST_HEBDO_HEURE    = "07:30"   # avant les emails quotidiens

# ── Sources globales — fiabilité (0-10) ───────────────────────
# Utilisées par tous les modèles — chaque modèle peut en
# activer/désactiver selon la disponibilité du modèle
SOURCES_FIABILITE = {
    "mercedes_certified" : 10,
    "autohero"           : 10,
    "aramisauto"         : 10,
    "spoticar"           : 10,
    "transakauto"        : 8,
    "elite_auto"         : 8,
    "jean_lain"          : 8,
    "zoomcar"            : 8,
    "capcar"             : 7,
    "autoscout24"        : 6,
    "lacentrale"         : 6,
    "autouncle"          : 5,
    "ewigo"              : 5,
    "simplicicar"        : 5,
    "leboncoin"          : 4,
}

# ── Régions prioritaires (communes) ───────────────────────────
REGIONS_PRIORITAIRES = ["Centre", "Ile-de-France", "Normandie"]
