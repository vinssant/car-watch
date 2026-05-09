# 🚗 car-watch

Système de veille automobile automatique multi-modèles, orienté TCO.
Un email quotidien par modèle surveillé + un digest hebdomadaire global.

---

## Modèles surveillés

| Modèle | Statut | Critères clés |
|--------|--------|---------------|
| 🚗 Mercedes C300e Break | ✅ **Actif** | 2023+ · ≤65k km · ≤42k€ · Toit ouvrant · Garantie 12 mois |
| 🏆 Toyota Corolla TS 2.0 HEV | ⏸️ Prêt | 2023+ · ≤60k km · ≤38k€ · Garantie 12 mois |
| 🥈 Skoda Superb IV Combi PHEV | ⏸️ Prêt | 2024+ · ≤50k km · ≤42k€ · Garantie 12 mois |

**Activer un modèle** : ouvrir `modeles/toyota_corolla_ts.py` → `"actif": True`

**Ajouter un nouveau modèle** : créer `modeles/mon_modele.py` en copiant un fichier existant

---

## Ce que vous recevez

### Email quotidien (par modèle actif — 8h00)
- 🆕 Nouvelles annonces avec score TCO
- 📉 Baisses de prix sur annonces déjà connues
- 🏆 Top 5 meilleures annonces actives
- 💨 Annonces disparues (vendues)
- 📌 Suivi manuel de vos annonces en cours
- 📊 Tendances marché (prix moyen, km moyen, durée avant vente)

### Digest hebdomadaire (lundi 7h30)
- Synthèse de tous les modèles actifs
- Statistiques de la semaine par modèle
- Top 3 annonces de la semaine par modèle

---

## Scoring TCO (0-100)

| Critère | Poids | Score max quand... |
|---------|-------|-------------------|
| Kilométrage | 25% | < 40% du km_ideal |
| Année | 20% | ≥ annee_min + 2 |
| Prix vs cote | 20% | > 12% sous la cote |
| Garantie | 15% | ≥ 24 mois |
| Équipements clés | 10% | Tous présents |
| Fiabilité source | 10% | Réseau officiel |

**Alertes** : 🔴 ≥85 (URGENT) · 🟠 ≥70 · 🟡 ≥50 · ⚪ <50 (ignoré)

---

## Installation

### 1. Cloner et installer

```bash
git clone https://github.com/VOTRE_USERNAME/car-watch.git
cd car-watch
pip install -r requirements.txt
```

### 2. Configurer Gmail OAuth2

```bash
# Placer credentials.json (Google Cloud Console) dans le dossier
python3 oauth_setup.py
# → token.json est créé → copier son contenu dans GitHub Secret GMAIL_TOKEN
```

### 3. Tester

```bash
python3 main.py --test                          # tous les modèles actifs
python3 main.py --test --modele mercedes_c300e  # un seul modèle
python3 main.py --digest                        # digest hebdo
```

### 4. GitHub Actions

GitHub → Settings → Secrets → `GMAIL_TOKEN` → coller contenu de `token.json`

Le workflow se déclenche automatiquement :
- Tous les jours à 8h00 (Paris) → veille quotidienne
- Tous les lundis à 7h30 (Paris) → digest hebdomadaire

---

## Structure

```
car-watch/
├── modeles/
│   ├── __init__.py              # chargeur automatique
│   ├── mercedes_c300e.py        # ✅ actif
│   ├── toyota_corolla_ts.py     # ⏸️ à activer
│   └── skoda_superb_combi.py    # ⏸️ à activer
├── scrapers/
│   ├── autohero.py
│   ├── aramisauto.py
│   └── autoscout24.py
├── core/
│   ├── scorer.py                # TCO générique
│   ├── deduplicator.py          # historique par modèle
│   ├── reporter.py              # emails HTML
│   └── mailer.py                # Gmail API
├── data/
│   ├── mercedes_c300e/          # historique isolé
│   │   ├── seen_ads.json
│   │   └── ads_history.json
│   ├── toyota_corolla_ts/
│   └── skoda_superb_combi/
├── config.py                    # paramètres globaux
├── main.py                      # orchestrateur
└── .github/workflows/veille.yml
```

---

## Commandes utiles

```bash
# Veille normale
python3 main.py

# Test (pas d'email)
python3 main.py --test

# Un seul modèle
python3 main.py --modele mercedes_c300e

# Digest hebdo
python3 main.py --digest
```

---

## Ajouter un nouveau modèle

1. Copier `modeles/toyota_corolla_ts.py` → `modeles/mon_nouveau_modele.py`
2. Modifier `MODELE["id"]`, `MODELE["nom"]`, `MODELE["criteres"]`, etc.
3. Mettre `MODELE["actif"] = True`
4. Committer → GitHub Actions l'intègre automatiquement au prochain run

---

*car-watch v1.0 · Veille TCO automobile multi-modèles · vinssant@gmail.com*
