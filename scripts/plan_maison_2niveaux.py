"""
Plan maison 2 niveaux - 4 chambres
RDC : Salon, Cuisine, Salle à manger, WC, Entrée
Étage : 4 Chambres, 2 Salles de bain, Couloir
"""

import sys
sys.path.insert(0, 'D:\\python_libs')

import ezdxf
from ezdxf.enums import TextEntityAlignment

def creer_plan_complet(nom_fichier="plan_maison_2niveaux.dxf"):
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # ── Calques ───────────────────────────────────────────────
    doc.layers.add("MURS",        color=7)
    doc.layers.add("PORTES",      color=1)
    doc.layers.add("FENETRES",    color=4)
    doc.layers.add("COTES",       color=3)
    doc.layers.add("TEXTES",      color=2)
    doc.layers.add("ESCALIER",    color=6)
    doc.layers.add("TITRE",       color=5)
    doc.layers.add("CARTOUCHE",   color=7)

    # ════════════════════════════════════════════════════════
    # RDC — plan à gauche, origine (0,0)
    # Maison 12m x 10m
    # ════════════════════════════════════════════════════════
    ox, oy = 0, 0

    def mur(x1,y1,x2,y2, ep=50):
        msp.add_line((ox+x1,oy+y1),(ox+x2,oy+y2),
                     dxfattribs={"layer":"MURS","lineweight":ep})

    def porte(x1,y1,x2,y2):
        msp.add_line((ox+x1,oy+y1),(ox+x2,oy+y2),
                     dxfattribs={"layer":"PORTES","lineweight":18})

    def fenetre(x1,y1,x2,y2):
        msp.add_line((ox+x1,oy+y1),(ox+x2,oy+y2),
                     dxfattribs={"layer":"FENETRES","lineweight":25})
        # double trait fenêtre
        dx = (x2-x1)*0.15; dy = (y2-y1)*0.15
        msp.add_line((ox+x1+dx,oy+y1+dy),(ox+x2-dx,oy+y2-dy),
                     dxfattribs={"layer":"FENETRES","lineweight":10})

    def texte(x,y,txt,h=0.35):
        msp.add_text(txt,dxfattribs={"layer":"TEXTES","height":h})\
           .set_placement((ox+x,oy+y),align=TextEntityAlignment.MIDDLE_CENTER)

    def titre_plan(x,y,txt,h=0.6):
        msp.add_text(txt,dxfattribs={"layer":"TITRE","height":h})\
           .set_placement((ox+x,oy+y),align=TextEntityAlignment.MIDDLE_CENTER)

    # ── RDC Murs extérieurs 12x10 ─────────────────────────
    mur(0,0,12,0); mur(12,0,12,10)
    mur(12,10,0,10); mur(0,10,0,0)

    # ── RDC Murs intérieurs ───────────────────────────────
    mur(0,4,7,4)          # séparation entrée/salon-cuisine
    mur(7,0,7,10)         # séparation salon/cuisine+SaM
    mur(7,6,12,6)         # séparation cuisine/salle à manger
    mur(0,7,4,7)          # WC

    # ── Portes RDC ────────────────────────────────────────
    porte(2,0,3,0)        # porte entrée
    porte(4,4,5,4)        # porte salon→entrée
    porte(7,2,7,3)        # porte cuisine
    porte(0,7,1,7)        # porte WC
    porte(0,4,0,5)        # porte entrée latérale

    # ── Fenêtres RDC ──────────────────────────────────────
    fenetre(1,10,3,10)    # fenêtre salon
    fenetre(5,10,7,10)    # fenêtre salon (grande)
    fenetre(8,10,11,10)   # fenêtre cuisine
    fenetre(8,0,11,0)     # fenêtre salle à manger
    fenetre(12,1,12,4)    # fenêtre côté droit
    fenetre(0,5,0,7)      # fenêtre entrée

    # ── Escalier RDC (3x2 à angle) ────────────────────────
    for i in range(9):
        msp.add_line((ox+4+i*0.33, oy+4.1),(ox+4+i*0.33, oy+5.9),
                     dxfattribs={"layer":"ESCALIER","lineweight":13})
    msp.add_line((ox+4,oy+4.1),(ox+7,oy+4.1),dxfattribs={"layer":"ESCALIER"})
    msp.add_line((ox+4,oy+5.9),(ox+7,oy+5.9),dxfattribs={"layer":"ESCALIER"})

    # ── Textes RDC ────────────────────────────────────────
    texte(3.5,2,  "SALON",       0.4)
    texte(3.5,8,  "ENTREE",      0.35)
    texte(2,5.5,  "WC",          0.3)
    texte(9.5,3,  "SALLE A",     0.3)
    texte(9.5,2.5,"MANGER",      0.3)
    texte(9.5,8,  "CUISINE",     0.4)
    texte(5.5,5,  "ESCALIER",   0.25)

    # ── Cotations RDC ─────────────────────────────────────
    msp.add_linear_dim(base=(ox+0,oy-1.5),p1=(ox+0,oy+0),p2=(ox+12,oy+0),
        dimstyle="Standard",dxfattribs={"layer":"COTES"}).render()
    msp.add_linear_dim(base=(ox-1.5,oy+0),p1=(ox+0,oy+0),p2=(ox+0,oy+10),
        angle=90,dimstyle="Standard",dxfattribs={"layer":"COTES"}).render()

    titre_plan(6, -2.5, "PLAN RDC — REZ-DE-CHAUSSEE", 0.55)

    # ════════════════════════════════════════════════════════
    # ÉTAGE — plan à droite, décalé de +16 en X
    # 4 Chambres + 2 SDB + couloir
    # ════════════════════════════════════════════════════════
    ox2, oy2 = 16, 0

    def mur2(x1,y1,x2,y2,ep=50):
        msp.add_line((ox2+x1,oy2+y1),(ox2+x2,oy2+y2),
                     dxfattribs={"layer":"MURS","lineweight":ep})

    def porte2(x1,y1,x2,y2):
        msp.add_line((ox2+x1,oy2+y1),(ox2+x2,oy2+y2),
                     dxfattribs={"layer":"PORTES","lineweight":18})

    def fenetre2(x1,y1,x2,y2):
        msp.add_line((ox2+x1,oy2+y1),(ox2+x2,oy2+y2),
                     dxfattribs={"layer":"FENETRES","lineweight":25})
        dx=(x2-x1)*0.15; dy=(y2-y1)*0.15
        msp.add_line((ox2+x1+dx,oy2+y1+dy),(ox2+x2-dx,oy2+y2-dy),
                     dxfattribs={"layer":"FENETRES","lineweight":10})

    def texte2(x,y,txt,h=0.35):
        msp.add_text(txt,dxfattribs={"layer":"TEXTES","height":h})\
           .set_placement((ox2+x,oy2+y),align=TextEntityAlignment.MIDDLE_CENTER)

    # ── Murs extérieurs étage 12x10 ───────────────────────
    mur2(0,0,12,0); mur2(12,0,12,10)
    mur2(12,10,0,10); mur2(0,10,0,0)

    # ── Murs intérieurs étage ─────────────────────────────
    mur2(0,5,12,5,30)      # couloir horizontal
    mur2(6,5,6,10,30)      # séparation ch1/ch2
    mur2(6,0,6,5,30)       # séparation ch3/ch4
    mur2(9,5,9,10,25)      # SDB 1
    mur2(9,0,9,5,25)       # SDB 2

    # ── Portes étage ──────────────────────────────────────
    porte2(2,5,3,5)        # porte ch1
    porte2(7.5,5,8.5,5)    # porte ch2
    porte2(2,5,3,5)        # porte ch3
    porte2(7,5,7,4)        # porte sdb2
    porte2(0,2,0,3)        # porte ch3 ext
    porte2(0,7,0,8)        # porte ch1 ext
    porte2(9,6,9,7)        # porte sdb1
    porte2(9,1,9,2)        # porte sdb2
    porte2(3,5,4,5)        # porte ch4

    # ── Fenêtres étage ────────────────────────────────────
    fenetre2(1,10,5,10)    # ch1 fenêtre
    fenetre2(7,10,9,10)    # sdb1 fenêtre
    fenetre2(10,10,12,10)  # ch2 fenêtre
    fenetre2(1,0,5,0)      # ch3 fenêtre
    fenetre2(7,0,9,0)      # sdb2 fenêtre
    fenetre2(10,0,12,0)    # ch4 fenêtre
    fenetre2(0,6,0,9)      # ch1 côté
    fenetre2(0,1,0,4)      # ch3 côté

    # ── Escalier étage ────────────────────────────────────
    for i in range(9):
        msp.add_line((ox2+4+i*0.33,oy2+4.1),(ox2+4+i*0.33,oy2+5.9),
                     dxfattribs={"layer":"ESCALIER","lineweight":13})
    msp.add_line((ox2+4,oy2+4.1),(ox2+7,oy2+4.1),dxfattribs={"layer":"ESCALIER"})
    msp.add_line((ox2+4,oy2+5.9),(ox2+7,oy2+5.9),dxfattribs={"layer":"ESCALIER"})

    # ── Textes étage ──────────────────────────────────────
    texte2(3,7.5,  "CHAMBRE 1",  0.4)
    texte2(3,7,    "16 m²",      0.28)
    texte2(10.5,7.5,"CHAMBRE 2", 0.4)
    texte2(10.5,7, "14 m²",      0.28)
    texte2(3,2.5,  "CHAMBRE 3",  0.4)
    texte2(3,2,    "16 m²",      0.28)
    texte2(10.5,2.5,"CHAMBRE 4", 0.4)
    texte2(10.5,2, "14 m²",      0.28)
    texte2(10.5,7.5,"SDB 1",     0.28)
    texte2(10.5,2, "SDB 2",      0.28)
    texte2(5.5,5,  "ESCALIER",  0.25)
    texte2(2,5.2,  "COULOIR",   0.3)

    # ── Cotations étage ───────────────────────────────────
    msp.add_linear_dim(base=(ox2+0,oy2-1.5),p1=(ox2+0,oy2+0),p2=(ox2+12,oy2+0),
        dimstyle="Standard",dxfattribs={"layer":"COTES"}).render()
    msp.add_linear_dim(base=(ox2+13.5,oy2+0),p1=(ox2+12,oy2+0),p2=(ox2+12,oy2+10),
        angle=90,dimstyle="Standard",dxfattribs={"layer":"COTES"}).render()

    msp.add_text("PLAN ETAGE — 1er NIVEAU",
                 dxfattribs={"layer":"TITRE","height":0.55})\
       .set_placement((ox2+6,oy2-2.5),align=TextEntityAlignment.MIDDLE_CENTER)

    # ════════════════════════════════════════════════════════
    # CARTOUCHE GENERAL
    # ════════════════════════════════════════════════════════
    cx, cy = 0, -6
    msp.add_lwpolyline(
        [(cx,cy),(cx+28,cy),(cx+28,cy+3),(cx,cy+3),(cx,cy)],
        dxfattribs={"layer":"CARTOUCHE","closed":True})
    msp.add_line((cx,cy+2),(cx+28,cy+2),dxfattribs={"layer":"CARTOUCHE"})
    msp.add_line((cx+14,cy),(cx+14,cy+2),dxfattribs={"layer":"CARTOUCHE"})
    msp.add_line((cx+21,cy),(cx+21,cy+2),dxfattribs={"layer":"CARTOUCHE"})

    champs = [
        (cx+14, cy+2.5, "MAISON INDIVIDUELLE — 2 NIVEAUX — 4 CHAMBRES", 0.45),
        (cx+7,  cy+1,   "Projet : Résidence familiale",    0.28),
        (cx+17.5,cy+1,  "Échelle : 1:100",                 0.28),
        (cx+24.5,cy+1,  "N° DWG : DWG-002",               0.28),
        (cx+7,  cy+0.4, "Dessiné par : Claude AI",         0.22),
        (cx+17.5,cy+0.4,"Date : 2026-05-17",              0.22),
        (cx+24.5,cy+0.4,"Révision : 01",                  0.22),
    ]
    for x,y,txt,h in champs:
        msp.add_text(txt,dxfattribs={"layer":"CARTOUCHE","height":h})\
           .set_placement((x,y),align=TextEntityAlignment.MIDDLE_CENTER)

    # ── Sauvegarder ───────────────────────────────────────
    doc.saveas(nom_fichier)
    print(f"✅ Plan généré : {nom_fichier}")
    print(f"   - RDC : Salon, Cuisine, Salle à manger, WC, Entrée, Escalier")
    print(f"   - Étage : 4 Chambres (16m² + 14m²), 2 SDB, Couloir, Escalier")
    print(f"   - Dimensions : 12m x 10m par niveau")
    print(f"   - Calques : MURS, PORTES, FENETRES, COTES, TEXTES, ESCALIER, CARTOUCHE")

if __name__ == "__main__":
    creer_plan_complet("plan_maison_2niveaux.dxf")
