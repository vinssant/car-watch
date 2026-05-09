# =============================================================
# modeles/__init__.py — Chargeur automatique des modèles
# Scanne le dossier modeles/ et retourne les modèles actifs
# Ajouter un modèle = créer un fichier .py avec MODELE = {...}
# =============================================================

import importlib
from pathlib import Path


def charger_modeles_actifs() -> list:
    """
    Charge automatiquement tous les modèles actifs.
    Scanne modeles/*.py, importe chaque fichier, retourne
    ceux dont modele["actif"] == True.
    """
    modeles = []
    dossier = Path(__file__).parent

    for fichier in sorted(dossier.glob("*.py")):
        if fichier.name.startswith("_"):
            continue

        nom_module = f"modeles.{fichier.stem}"
        try:
            module = importlib.import_module(nom_module)
            if hasattr(module, "MODELE") and module.MODELE.get("actif", False):
                modeles.append(module.MODELE)
                print(f"  ✅ Modèle chargé : {module.MODELE['nom']}")
            else:
                print(f"  ⏸️  Modèle inactif : {fichier.stem}")
        except Exception as e:
            print(f"  ❌ Erreur chargement {fichier.stem} : {e}")

    return modeles


def charger_tous_modeles() -> list:
    """Charge tous les modèles, actifs ou non (pour le digest hebdo)."""
    modeles = []
    dossier = Path(__file__).parent

    for fichier in sorted(dossier.glob("*.py")):
        if fichier.name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"modeles.{fichier.stem}")
            if hasattr(module, "MODELE"):
                modeles.append(module.MODELE)
        except Exception:
            pass

    return modeles