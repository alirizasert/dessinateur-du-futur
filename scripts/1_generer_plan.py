"""
Script 1 : Générer un plan d'architecture automatiquement
Bibliothèque : ezdxf
Installation : pip install ezdxf
"""

import ezdxf
from ezdxf.enums import TextEntityAlignment

def creer_plan_maison(nom_fichier="plan_maison.dxf"):
    # Créer un nouveau document DXF
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # ── Créer les calques ──────────────────────────────────────
    doc.layers.add("MURS",       color=7)   # blanc
    doc.layers.add("PORTES",     color=1)   # rouge
    doc.layers.add("FENETRES",   color=4)   # cyan
    doc.layers.add("COTES",      color=3)   # vert
    doc.layers.add("TEXTES",     color=2)   # jaune

    # ── Murs extérieurs (rectangle 10m x 8m) ─────────────────
    murs = [
        [(0, 0),   (10, 0)],   # mur bas
        [(10, 0),  (10, 8)],   # mur droit
        [(10, 8),  (0, 8)],    # mur haut
        [(0, 8),   (0, 0)],    # mur gauche
    ]
    for debut, fin in murs:
        msp.add_line(debut, fin, dxfattribs={"layer": "MURS", "lineweight": 50})

    # ── Mur de séparation (couloir) ───────────────────────────
    msp.add_line((5, 0), (5, 8), dxfattribs={"layer": "MURS", "lineweight": 30})
    msp.add_line((0, 4), (5, 4), dxfattribs={"layer": "MURS", "lineweight": 30})

    # ── Portes ────────────────────────────────────────────────
    # Porte d'entrée (bas, milieu)
    msp.add_line((4.5, 0), (5.5, 0), dxfattribs={"layer": "PORTES"})
    msp.add_arc((4.5, 0), radius=1, start_angle=0, end_angle=90,
                dxfattribs={"layer": "PORTES"})

    # Porte intérieure salon
    msp.add_line((5, 1.5), (5, 2.5), dxfattribs={"layer": "PORTES"})
    msp.add_arc((5, 2.5), radius=1, start_angle=180, end_angle=270,
                dxfattribs={"layer": "PORTES"})

    # ── Fenêtres ──────────────────────────────────────────────
    fenetres = [
        [(1, 8), (3, 8)],   # fenêtre chambre 1
        [(6, 8), (9, 8)],   # fenêtre salon
        [(10, 2), (10, 5)], # fenêtre droite
    ]
    for debut, fin in fenetres:
        milieu = ((debut[0]+fin[0])/2, (debut[1]+fin[1])/2)
        msp.add_line(debut, fin, dxfattribs={"layer": "FENETRES", "lineweight": 25})

    # ── Cotations ─────────────────────────────────────────────
    dim_style = doc.dimstyles.get("Standard")
    msp.add_linear_dim(
        base=(0, -1.5),
        p1=(0, 0),
        p2=(10, 0),
        dimstyle="Standard",
        dxfattribs={"layer": "COTES"}
    ).render()

    msp.add_linear_dim(
        base=(-1.5, 0),
        p1=(0, 0),
        p2=(0, 8),
        angle=90,
        dimstyle="Standard",
        dxfattribs={"layer": "COTES"}
    ).render()

    # ── Textes / étiquettes des pièces ────────────────────────
    pieces = [
        ((2.5, 6),   "CHAMBRE 1"),
        ((2.5, 2),   "CHAMBRE 2"),
        ((7.5, 4),   "SALON"),
        ((7.5, 1.5), "CUISINE"),
        ((2.5, 4.5), "COULOIR"),
    ]
    for pos, nom in pieces:
        msp.add_text(
            nom,
            dxfattribs={
                "layer": "TEXTES",
                "height": 0.3,
                "color": 2,
            }
        ).set_placement(pos, align=TextEntityAlignment.MIDDLE_CENTER)

    # ── Titre du plan ─────────────────────────────────────────
    msp.add_text(
        "PLAN RDC - MAISON",
        dxfattribs={"layer": "TEXTES", "height": 0.5}
    ).set_placement((5, -2.5), align=TextEntityAlignment.MIDDLE_CENTER)

    # ── Sauvegarder ───────────────────────────────────────────
    doc.saveas(nom_fichier)
    print(f"Plan généré : {nom_fichier}")
    print(f"Calques créés : MURS, PORTES, FENETRES, COTES, TEXTES")

if __name__ == "__main__":
    creer_plan_maison("plan_maison.dxf")
