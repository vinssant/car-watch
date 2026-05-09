# =============================================================
# core/reporter.py — Génération emails HTML
# Email quotidien par modèle + digest hebdomadaire global
# =============================================================

from datetime import datetime
from config import SCORING_DEFAULT, SCORE_URGENT, SCORE_ALERTE, SCORE_INFO

CSS = """
body{font-family:Arial,sans-serif;background:#f4f5f7;margin:0;padding:16px;color:#1a1a2e}
.wrap{max-width:700px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,.1)}
.hdr{padding:24px 28px;color:#fff}
.hdr h1{margin:0 0 5px;font-size:20px}
.hdr p{margin:0;font-size:12px;opacity:.8}
.sec{background:#f0f4f8;padding:8px 28px;font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#64748b;border-top:1px solid #e2e8f0}
.card{border-bottom:1px solid #f1f5f9;padding:15px 28px}
.card-urgent{background:#fff5f5;border-left:4px solid #dc2626}
.card-alerte{background:#fffbeb;border-left:4px solid #d97706}
.card-info{background:#f0fdf4;border-left:4px solid #16a34a}
.card-neutre{border-left:4px solid #e2e8f0}
.card-disparue{background:#f8fafc;border-left:4px solid #94a3b8;opacity:.7}
.title{font-size:15px;font-weight:600;color:#1a1a2e;margin:5px 0 3px}
.meta{font-size:12px;color:#64748b;margin:0 0 8px}
.specs{display:flex;flex-wrap:wrap;gap:4px;margin:7px 0}
.spec{background:#f1f5f9;border-radius:4px;padding:2px 7px;font-size:11px;color:#475569}
.spec-ok{background:#dcfce7;color:#166534;font-weight:600}
.spec-warn{background:#fef3c7;color:#92400e}
.spec-bad{background:#fee2e2;color:#991b1b}
.prix{font-size:18px;font-weight:700;color:#1e40af}
.prix-baisse{color:#16a34a}
.reco{background:#f8fafc;border-radius:6px;padding:7px 11px;font-size:12px;color:#475569;margin:7px 0;line-height:1.6}
.btn{display:inline-block;margin-top:9px;padding:6px 14px;background:#1a1a2e;color:#fff !important;border-radius:5px;text-decoration:none;font-size:12px;font-weight:600}
.stat-row{display:flex;gap:10px;padding:14px 28px;flex-wrap:wrap}
.stat{background:#f8fafc;border-radius:8px;padding:11px 14px;flex:1;min-width:100px;text-align:center}
.stat-val{font-size:21px;font-weight:700;color:#1a1a2e}
.stat-lbl{font-size:11px;color:#64748b;margin-top:2px}
.prog{background:#e2e8f0;border-radius:3px;height:4px;margin:5px 0 2px;overflow:hidden}
.prog-fill{height:100%;border-radius:3px}
.ftr{background:#f0f4f8;padding:12px 28px;font-size:11px;color:#94a3b8;text-align:center;border-top:1px solid #e2e8f0}
.modele-badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;margin-bottom:8px}
"""


def _fmt_prix(p) -> str:
    if p is None:
        return "Prix à confirmer"
    return f"{int(p):,} €".replace(",", " ")


def _fmt_km(k) -> str:
    if k is None:
        return "? km"
    return f"{int(k):,} km".replace(",", " ")


def _couleur_score(score: float) -> str:
    if score >= 85:
        return "#dc2626"
    if score >= 70:
        return "#d97706"
    if score >= 50:
        return "#16a34a"
    return "#94a3b8"


def _carte_annonce(annonce: dict, style: str = "card-neutre") -> str:
    score   = annonce.get("score_total", 0)
    titre   = annonce.get("titre", "Sans titre")
    vendeur = annonce.get("vendeur", "Vendeur inconnu")
    source  = annonce.get("source", "")
    prix    = annonce.get("prix")
    km      = annonce.get("km")
    annee   = annonce.get("annee", "")
    garantie= annonce.get("garantie_mois")
    url     = annonce.get("url", "#")
    reco    = annonce.get("recommandation", "")
    niveau  = annonce.get("niveau_alerte", "INFO")
    couleur = _couleur_score(score)

    # Prix avec variation
    prix_html = f'<span class="prix">{_fmt_prix(prix)}</span>'
    if annonce.get("prix_baisse") and annonce.get("prix_precedent"):
        pct = abs(annonce.get("prix_variation_pct", 0))
        prix_html = (
            f'<span class="prix prix-baisse">{_fmt_prix(prix)}</span> '
            f'<span style="text-decoration:line-through;color:#94a3b8;font-size:13px">'
            f'{_fmt_prix(annonce["prix_precedent"])}</span> '
            f'<span style="color:#16a34a;font-size:12px;font-weight:600">▼ {pct}%</span>'
        )

    garantie_spec = ""
    if garantie:
        cls = "spec-ok" if garantie >= 12 else "spec-warn"
        garantie_spec = f'<span class="spec {cls}">Garantie {garantie} mois</span>'

    return f"""
    <div class="card {style}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:6px">
        <div>
          <span style="background:{couleur};color:#fff;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:700">{niveau} · {score}/100</span>
          <div class="title">{titre}</div>
          <div class="meta">{vendeur}{f' · {source}' if source else ''}</div>
        </div>
        <div style="text-align:right">
          {prix_html}
          <div style="font-size:11px;color:#94a3b8">{_fmt_km(km)}{f' · {annee}' if annee else ''}</div>
        </div>
      </div>
      <div class="specs">{garantie_spec}</div>
      <div class="prog"><div class="prog-fill" style="width:{score}%;background:{couleur}"></div></div>
      {'<div class="reco">' + reco + '</div>' if reco else ''}
      <a href="{url}" class="btn">Voir l'annonce →</a>
    </div>"""


def generer_email_modele(modele: dict, resultats: dict, stats_marche: dict = None) -> str:
    """Email quotidien pour un modèle spécifique."""
    date      = datetime.now().strftime("%d/%m/%Y à %H:%M")
    nouvelles = resultats.get("nouvelles", [])
    baisses   = resultats.get("prix_baisses", [])
    disparues = resultats.get("disparues", [])
    toutes    = resultats.get("toutes_actives", [])
    stats     = resultats.get("stats", {})

    # Couleur thématique par modèle
    couleurs = {
        "mercedes_c300e"    : "#1a1a2e",
        "toyota_corolla_ts" : "#cc0000",
        "skoda_superb_combi": "#4caf50",
    }
    couleur_hdr = couleurs.get(modele["id"], "#1a1a2e")

    nb_urgentes = sum(1 for a in nouvelles + baisses if a.get("niveau_alerte") == "URGENT")

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>{CSS}</style></head><body><div class="wrap">

<div class="hdr" style="background:{couleur_hdr}">
  <h1>{modele['emoji']} {modele['nom']} — Veille quotidienne</h1>
  <p>{date} · {modele['description']}</p>
</div>

<div class="stat-row">
  <div class="stat">
    <div class="stat-val" style="color:{'#dc2626' if nb_urgentes else '#d97706' if nouvelles else '#16a34a'}">{len(nouvelles)}</div>
    <div class="stat-lbl">Nouvelles</div>
  </div>
  <div class="stat">
    <div class="stat-val" style="color:#16a34a">{len(baisses)}</div>
    <div class="stat-lbl">Baisses prix</div>
  </div>
  <div class="stat">
    <div class="stat-val">{stats.get('total_actives', len(toutes))}</div>
    <div class="stat-lbl">Total actives</div>
  </div>
  <div class="stat">
    <div class="stat-val" style="color:#94a3b8">{len(disparues)}</div>
    <div class="stat-lbl">Disparues</div>
  </div>
</div>"""

    # Nouvelles annonces
    if nouvelles:
        html += '<div class="sec">🆕 Nouvelles annonces</div>'
        for a in nouvelles:
            s = {"URGENT": "card-urgent", "ALERTE": "card-alerte"}.get(a.get("niveau_alerte"), "card-info")
            html += _carte_annonce(a, s)
    else:
        html += '<div class="card" style="text-align:center;color:#94a3b8;padding:18px">Aucune nouvelle annonce aujourd\'hui</div>'

    # Baisses de prix
    if baisses:
        html += f'<div class="sec">📉 Baisses de prix ({len(baisses)})</div>'
        for a in baisses:
            html += _carte_annonce(a, "card-info")

    # Top 5
    top5 = sorted(toutes, key=lambda a: a.get("score_total", 0), reverse=True)[:5]
    if top5:
        html += '<div class="sec">🏆 Top 5 — Meilleures annonces actives</div>'
        for i, a in enumerate(top5, 1):
            score = a.get("score_total", 0)
            c     = _couleur_score(score)
            html += f"""
            <div class="card card-neutre">
              <div style="display:flex;align-items:center;gap:10px">
                <span style="font-size:20px;font-weight:700;color:#e2e8f0">#{i}</span>
                <div style="flex:1">
                  <span style="background:{c};color:#fff;padding:2px 6px;border-radius:3px;font-size:10px;font-weight:700">{score}/100</span>
                  <div class="title" style="font-size:14px">{a.get('titre','?')}</div>
                  <div class="meta">{a.get('vendeur','')} · {_fmt_prix(a.get('prix'))} · {_fmt_km(a.get('km'))}</div>
                </div>
              </div>
              <a href="{a.get('url','#')}" class="btn" style="margin-top:8px">Voir →</a>
            </div>"""

    # Annonces disparues
    if disparues:
        html += f'<div class="sec">💨 Annonces disparues ({len(disparues)}) — Vendues ou retirées</div>'
        for a in disparues[:3]:
            html += f"""
            <div class="card card-disparue">
              <div class="title" style="text-decoration:line-through;color:#94a3b8">{a.get('titre','?')}</div>
              <div class="meta">{a.get('source','')} · {_fmt_prix(a.get('prix'))} · {_fmt_km(a.get('km'))}</div>
            </div>"""

    # Stats marché
    if stats_marche and stats_marche.get("prix_moyen"):
        html += '<div class="sec">📊 Tendances marché</div>'
        html += f"""
        <div class="card">
          <div style="font-size:12px;line-height:2;color:#475569">
            💶 Prix moyen : <strong>{_fmt_prix(stats_marche.get('prix_moyen'))}</strong> &nbsp;·&nbsp;
            🛣️ Km moyen : <strong>{_fmt_km(stats_marche.get('km_moyen'))}</strong><br>
            ⏱️ Durée moy. avant vente : <strong>{stats_marche.get('duree_moy_marche_jours', '?')} jours</strong> &nbsp;·&nbsp;
            📉 Baisses enregistrées : <strong>{stats_marche.get('total_baisses_prix', 0)}</strong>
          </div>
        </div>"""

    # Suivi manuel
    suivies = modele.get("annonces_suivies", [])
    if suivies:
        html += '<div class="sec">📌 Suivi manuel</div>'
        couleurs_statut = {
            "PRIORITE_ABSOLUE": "#dc2626", "A_CONTACTER": "#d97706",
            "CONTACT_EN_COURS": "#2563eb", "VISITE_PLANIFIEE": "#7c3aed",
            "OFFRE_FAITE": "#059669", "A_VERIFIER": "#f59e0b",
        }
        for a in suivies:
            statut = a.get("statut", "")
            c_st   = couleurs_statut.get(statut, "#64748b")
            html  += f"""
            <div class="card card-neutre">
              <span style="background:{c_st};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">{statut}</span>
              <div class="title">{a.get('titre','?')}</div>
              <div class="meta">{a.get('vendeur','')} · {_fmt_prix(a.get('prix'))} · {_fmt_km(a.get('km'))}</div>
              {'<div class="reco">' + a["notes"] + '</div>' if a.get("notes") else ''}
              <a href="{a.get('url','#')}" class="btn">Voir →</a>
            </div>"""

    criteres = modele.get("criteres", {})
    html += f"""
<div class="ftr">
  {modele['emoji']} {modele['nom']} · car-watch · {date}<br>
  Critères : ≥{criteres.get('annee_min','?')} · ≤{criteres.get('km_max','?')} km · ≤{criteres.get('budget_max','?')} € · Garantie ≥{criteres.get('garantie_min_mois','?')} mois
</div></div></body></html>"""

    return html


def generer_digest_hebdo(resultats_par_modele: list) -> str:
    """Email digest hebdomadaire groupant tous les modèles actifs."""
    date = datetime.now().strftime("Semaine du %d/%m/%Y")

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>{CSS}
.modele-section{{border:2px solid #e2e8f0;border-radius:10px;margin:16px 28px;overflow:hidden}}
.modele-hdr{{padding:14px 18px;color:#fff;display:flex;align-items:center;gap:10px}}
</style></head><body><div class="wrap">

<div class="hdr" style="background:linear-gradient(135deg,#1a1a2e,#2d3561)">
  <h1>📊 car-watch — Digest hebdomadaire</h1>
  <p>{date} · Synthèse de tous les modèles surveillés</p>
</div>"""

    couleurs = {
        "mercedes_c300e"    : "#1a1a2e",
        "toyota_corolla_ts" : "#cc0000",
        "skoda_superb_combi": "#2e7d32",
    }

    for item in resultats_par_modele:
        modele    = item["modele"]
        resultats = item["resultats"]
        stats     = item.get("stats", {})
        toutes    = resultats.get("toutes_actives", [])
        nouvelles_sem = item.get("nouvelles_semaine", 0)
        disparues_sem = item.get("disparues_semaine", 0)
        baisses_sem   = item.get("baisses_semaine", 0)

        top3 = sorted(toutes, key=lambda a: a.get("score_total", 0), reverse=True)[:3]
        couleur = couleurs.get(modele["id"], "#1a1a2e")

        html += f"""
        <div class="modele-section">
          <div class="modele-hdr" style="background:{couleur}">
            <span style="font-size:22px">{modele['emoji']}</span>
            <div>
              <div style="font-size:15px;font-weight:700">{modele['nom']}</div>
              <div style="font-size:11px;opacity:.8">{modele['description']}</div>
            </div>
          </div>

          <div class="stat-row" style="padding:12px 16px">
            <div class="stat"><div class="stat-val">{nouvelles_sem}</div><div class="stat-lbl">Nouvelles/sem</div></div>
            <div class="stat"><div class="stat-val" style="color:#16a34a">{baisses_sem}</div><div class="stat-lbl">Baisses prix</div></div>
            <div class="stat"><div class="stat-val" style="color:#94a3b8">{disparues_sem}</div><div class="stat-lbl">Disparues</div></div>
            <div class="stat"><div class="stat-val">{len(toutes)}</div><div class="stat-lbl">Total actives</div></div>
          </div>"""

        if stats.get("prix_moyen"):
            html += f"""
          <div style="padding:0 16px 12px;font-size:12px;color:#475569">
            💶 Prix moyen : <strong>{_fmt_prix(stats.get('prix_moyen'))}</strong> &nbsp;·&nbsp;
            🛣️ Km moyen : <strong>{_fmt_km(stats.get('km_moyen'))}</strong> &nbsp;·&nbsp;
            ⏱️ Durée moy. : <strong>{stats.get('duree_moy_marche_jours','?')} j</strong>
          </div>"""

        if top3:
            html += '<div style="padding:0 16px 8px;font-size:10px;font-weight:700;letter-spacing:.07em;color:#94a3b8;text-transform:uppercase">🏆 Top 3 de la semaine</div>'
            for i, a in enumerate(top3, 1):
                score = a.get("score_total", 0)
                c     = _couleur_score(score)
                html += f"""
            <div style="padding:10px 16px;border-top:1px solid #f1f5f9;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">
              <div>
                <span style="background:{c};color:#fff;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:700">#{i} · {score}/100</span>
                <div style="font-size:13px;font-weight:600;margin:3px 0">{a.get('titre','?')}</div>
                <div style="font-size:11px;color:#64748b">{a.get('vendeur','')} · {_fmt_prix(a.get('prix'))} · {_fmt_km(a.get('km'))}</div>
              </div>
              <a href="{a.get('url','#')}" class="btn">Voir →</a>
            </div>"""

        html += "</div>"

    html += f"""
<div class="ftr">
  📊 car-watch — Digest hebdomadaire · {date}<br>
  Pour modifier les critères ou activer un nouveau modèle → éditer modeles/ sur GitHub
</div></div></body></html>"""

    return html


def generer_sujet_email(modele: dict, resultats: dict) -> str:
    date      = datetime.now().strftime("%d/%m/%Y")
    nouvelles = resultats.get("nouvelles", [])
    baisses   = resultats.get("prix_baisses", [])
    urgentes  = sum(1 for a in nouvelles + baisses if a.get("niveau_alerte") == "URGENT")

    if urgentes:
        return f"🔴 URGENT {modele['emoji']} {modele['nom']} — {urgentes} top TCO | {date}"
    if nouvelles:
        return f"🟠 {len(nouvelles)} nouvelle(s) {modele['emoji']} {modele['nom']} | {date}"
    if baisses:
        return f"📉 {len(baisses)} baisse(s) prix {modele['emoji']} {modele['nom']} | {date}"
    return f"🟡 Veille {modele['emoji']} {modele['nom']} | {date}"


def generer_sujet_digest() -> str:
    return f"📊 car-watch — Digest hebdo | {datetime.now().strftime('%d/%m/%Y')}"
