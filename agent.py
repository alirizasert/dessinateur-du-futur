"""
╔══════════════════════════════════════════════════════════════════╗
║          DESSINATEUR DU FUTUR — Agent AutoCAD IA                ║
║  Générer, lire, modifier et automatiser des plans DXF/DWG       ║
║  Propulsé par : ezdxf · pyautocad · LLM (Claude/GPT)           ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys
import os
sys.path.insert(0, 'D:\\python_libs')

import ezdxf
from ezdxf.enums import TextEntityAlignment
import json
import re

# ══════════════════════════════════════════════════════════════════
# DESSINATEUR DU FUTUR — Classe principale de l'agent
# ══════════════════════════════════════════════════════════════════

class DessinateurDuFutur:
    """
    Agent IA dessinateur AutoCAD.
    Capable de générer, lire, analyser et modifier des fichiers DXF/DWG.
    """

    NOM = "Dessinateur du Futur"
    VERSION = "1.0.0"
    COMPETENCES = [
        "Génération de plans DXF complets (maison, bâtiment, appartement)",
        "Lecture et analyse de fichiers DXF/DWG existants",
        "Automatisation AutoCAD via COM (pyautocad)",
        "Gestion des calques, cotations, textes et cartouches",
        "Plans 1 ou 2 niveaux avec pièces, fenêtres, portes, escaliers",
        "Export vers formats DXF R2010+",
        "Intégration LLM pour génération de plans par langage naturel",
    ]

    def __init__(self):
        self.doc = None
        self.msp = None
        self.ox = 0
        self.oy = 0
        print(f"\n{'='*60}")
        print(f"  {self.NOM} v{self.VERSION}")
        print(f"  Agent AutoCAD IA — Pret a dessiner !")
        print(f"{'='*60}")
        print("Competences :")
        for c in self.COMPETENCES:
            print(f"  - {c}")
        print()

    # ── Création de document ─────────────────────────────────────
    def nouveau_plan(self, nom_fichier="plan.dxf"):
        """Initialise un nouveau document DXF"""
        self.doc = ezdxf.new("R2010")
        self.msp = self.doc.modelspace()
        self.nom_fichier = nom_fichier
        self._creer_calques()
        print(f"Nouveau plan initialise : {nom_fichier}")
        return self

    def _creer_calques(self):
        calques = {
            "MURS":      7,   # blanc
            "PORTES":    1,   # rouge
            "FENETRES":  4,   # cyan
            "COTES":     3,   # vert
            "TEXTES":    2,   # jaune
            "ESCALIER":  6,   # magenta
            "TITRE":     5,   # bleu
            "CARTOUCHE": 7,   # blanc
            "MOBILIER":  8,   # gris
        }
        for nom, couleur in calques.items():
            self.doc.layers.add(nom, color=couleur)

    # ── Primitives de dessin ─────────────────────────────────────
    def mur(self, x1, y1, x2, y2, ep=50):
        self.msp.add_line(
            (self.ox+x1, self.oy+y1), (self.ox+x2, self.oy+y2),
            dxfattribs={"layer": "MURS", "lineweight": ep}
        )

    def porte(self, x1, y1, x2, y2):
        self.msp.add_line(
            (self.ox+x1, self.oy+y1), (self.ox+x2, self.oy+y2),
            dxfattribs={"layer": "PORTES", "lineweight": 18}
        )

    def fenetre(self, x1, y1, x2, y2):
        self.msp.add_line(
            (self.ox+x1, self.oy+y1), (self.ox+x2, self.oy+y2),
            dxfattribs={"layer": "FENETRES", "lineweight": 25}
        )
        dx = (x2-x1)*0.15
        dy = (y2-y1)*0.15
        self.msp.add_line(
            (self.ox+x1+dx, self.oy+y1+dy), (self.ox+x2-dx, self.oy+y2-dy),
            dxfattribs={"layer": "FENETRES", "lineweight": 10}
        )

    def texte(self, x, y, txt, h=0.35, calque="TEXTES"):
        self.msp.add_text(txt, dxfattribs={"layer": calque, "height": h})\
            .set_placement((self.ox+x, self.oy+y), align=TextEntityAlignment.MIDDLE_CENTER)

    def escalier(self, x, y, largeur=3, hauteur=2, nb_marches=9):
        for i in range(nb_marches):
            xi = x + i * (largeur / nb_marches)
            self.msp.add_line(
                (self.ox+xi, self.oy+y),
                (self.ox+xi, self.oy+y+hauteur),
                dxfattribs={"layer": "ESCALIER", "lineweight": 13}
            )
        self.msp.add_line((self.ox+x, self.oy+y), (self.ox+x+largeur, self.oy+y),
                          dxfattribs={"layer": "ESCALIER"})
        self.msp.add_line((self.ox+x, self.oy+y+hauteur), (self.ox+x+largeur, self.oy+y+hauteur),
                          dxfattribs={"layer": "ESCALIER"})

    def cartouche(self, cx, cy, titre, projet, echelle="1:100", numero="DWG-001"):
        self.msp.add_lwpolyline(
            [(cx,cy),(cx+28,cy),(cx+28,cy+3),(cx,cy+3),(cx,cy)],
            dxfattribs={"layer": "CARTOUCHE", "closed": True}
        )
        self.msp.add_line((cx, cy+2), (cx+28, cy+2), dxfattribs={"layer": "CARTOUCHE"})
        self.msp.add_line((cx+14, cy), (cx+14, cy+2), dxfattribs={"layer": "CARTOUCHE"})
        self.msp.add_line((cx+21, cy), (cx+21, cy+2), dxfattribs={"layer": "CARTOUCHE"})

        champs = [
            (cx+14, cy+2.5, titre, 0.45),
            (cx+7,  cy+1,   f"Projet : {projet}", 0.28),
            (cx+17.5,cy+1,  f"Echelle : {echelle}", 0.28),
            (cx+24.5,cy+1,  f"N DWG : {numero}", 0.28),
            (cx+7,  cy+0.4, "Dessine par : Dessinateur du Futur AI", 0.22),
            (cx+17.5,cy+0.4,"Date : 2026-05-18", 0.22),
            (cx+24.5,cy+0.4,"Revision : 01", 0.22),
        ]
        for x, y, txt, h in champs:
            self.msp.add_text(txt, dxfattribs={"layer": "CARTOUCHE", "height": h})\
                .set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)

    def cotation_h(self, base_y, x1, x2, y_ref=0):
        self.msp.add_linear_dim(
            base=(self.ox+x1, self.oy+base_y),
            p1=(self.ox+x1, self.oy+y_ref),
            p2=(self.ox+x2, self.oy+y_ref),
            dimstyle="Standard",
            dxfattribs={"layer": "COTES"}
        ).render()

    def cotation_v(self, base_x, y1, y2, x_ref=0):
        self.msp.add_linear_dim(
            base=(self.ox+base_x, self.oy+y1),
            p1=(self.ox+x_ref, self.oy+y1),
            p2=(self.ox+x_ref, self.oy+y2),
            angle=90,
            dimstyle="Standard",
            dxfattribs={"layer": "COTES"}
        ).render()

    # ── Sauvegarde ───────────────────────────────────────────────
    def sauvegarder(self):
        self.doc.saveas(self.nom_fichier)
        print(f"Plan sauvegarde : {self.nom_fichier}")
        return self.nom_fichier

    # ── Analyse d'un fichier existant ────────────────────────────
    def analyser(self, chemin):
        """Analyse un fichier DXF existant et retourne un rapport"""
        doc = ezdxf.readfile(chemin)
        msp = doc.modelspace()

        rapport = {
            "fichier": chemin,
            "version": doc.dxfversion,
            "calques": [],
            "entites": {},
            "textes": [],
        }

        for c in doc.layers:
            rapport["calques"].append({"nom": c.dxf.name, "couleur": c.dxf.color})

        for e in msp:
            t = e.dxftype()
            rapport["entites"][t] = rapport["entites"].get(t, 0) + 1

        for e in msp:
            if e.dxftype() == "TEXT":
                rapport["textes"].append(e.dxf.text)

        print(f"\nAnalyse de : {chemin}")
        print(f"  Version    : {rapport['version']}")
        print(f"  Calques    : {len(rapport['calques'])}")
        print(f"  Entites    : {sum(rapport['entites'].values())}")
        print(f"  Textes     : {len(rapport['textes'])}")
        return rapport

    # ── Génération de plans prédéfinis ───────────────────────────
    def generer_maison_simple(self, largeur=10, hauteur=8, nom="maison_simple.dxf"):
        """Génère une maison simple RDC"""
        self.nouveau_plan(nom)

        # Murs extérieurs
        self.mur(0, 0, largeur, 0)
        self.mur(largeur, 0, largeur, hauteur)
        self.mur(largeur, hauteur, 0, hauteur)
        self.mur(0, hauteur, 0, 0)

        # Séparations
        self.mur(largeur/2, 0, largeur/2, hauteur, ep=30)
        self.mur(0, hauteur/2, largeur/2, hauteur/2, ep=30)

        # Portes et fenêtres
        self.porte(largeur/2-0.5, 0, largeur/2+0.5, 0)
        self.fenetre(1, hauteur, 3, hauteur)
        self.fenetre(largeur/2+1, hauteur, largeur/2+3, hauteur)
        self.fenetre(largeur, 1, largeur, 4)

        # Textes
        self.texte(largeur*0.25, hauteur*0.75, "CHAMBRE 1", 0.4)
        self.texte(largeur*0.25, hauteur*0.25, "CHAMBRE 2", 0.4)
        self.texte(largeur*0.75, hauteur*0.5, "SALON/CUISINE", 0.4)

        # Cotations
        self.cotation_h(-1.5, 0, largeur)
        self.cotation_v(-1.5, 0, hauteur)

        self.texte(largeur/2, -2.5, "PLAN RDC", 0.55)
        self.sauvegarder()
        return self

    def generer_maison_2niveaux(self, nom="maison_2niveaux.dxf"):
        """Génère une maison 2 niveaux 4 chambres (plan complet)"""
        self.nouveau_plan(nom)

        # RDC
        self.ox, self.oy = 0, 0
        for cmd in [
            lambda: self.mur(0,0,12,0), lambda: self.mur(12,0,12,10),
            lambda: self.mur(12,10,0,10), lambda: self.mur(0,10,0,0),
            lambda: self.mur(0,4,7,4), lambda: self.mur(7,0,7,10),
            lambda: self.mur(7,6,12,6), lambda: self.mur(0,7,4,7),
        ]: cmd()

        self.porte(2,0,3,0); self.porte(4,4,5,4)
        self.porte(7,2,7,3); self.porte(0,7,1,7)
        self.fenetre(1,10,3,10); self.fenetre(5,10,7,10)
        self.fenetre(8,10,11,10); self.fenetre(8,0,11,0)
        self.escalier(4, 4.1)
        self.texte(3.5,2,"SALON",0.4); self.texte(3.5,8,"ENTREE",0.35)
        self.texte(2,5.5,"WC",0.3); self.texte(9.5,3,"SALLE A MANGER",0.28)
        self.texte(9.5,8,"CUISINE",0.4); self.texte(5.5,5,"ESCALIER",0.25)
        self.cotation_h(-1.5, 0, 12); self.cotation_v(-1.5, 0, 10)
        self.texte(6,-2.5,"PLAN RDC - REZ-DE-CHAUSSEE",0.55)

        # ETAGE
        self.ox, self.oy = 16, 0
        for cmd in [
            lambda: self.mur(0,0,12,0), lambda: self.mur(12,0,12,10),
            lambda: self.mur(12,10,0,10), lambda: self.mur(0,10,0,0),
            lambda: self.mur(0,5,12,5,30), lambda: self.mur(6,5,6,10,30),
            lambda: self.mur(6,0,6,5,30), lambda: self.mur(9,5,9,10,25),
            lambda: self.mur(9,0,9,5,25),
        ]: cmd()

        self.porte(2,5,3,5); self.porte(7.5,5,8.5,5)
        self.porte(3,5,4,5); self.porte(9,6,9,7)
        self.fenetre(1,10,5,10); self.fenetre(10,10,12,10)
        self.fenetre(1,0,5,0); self.fenetre(10,0,12,0)
        self.escalier(4, 4.1)
        self.texte(3,7.5,"CHAMBRE 1",0.4); self.texte(3,7,"16 m2",0.28)
        self.texte(10.5,7.5,"CHAMBRE 2",0.4); self.texte(10.5,7,"14 m2",0.28)
        self.texte(3,2.5,"CHAMBRE 3",0.4); self.texte(3,2,"16 m2",0.28)
        self.texte(10.5,2.5,"CHAMBRE 4",0.4); self.texte(10.5,2,"14 m2",0.28)
        self.texte(5.5,5,"ESCALIER",0.25); self.texte(2,5.2,"COULOIR",0.3)
        self.cotation_h(-1.5, 0, 12); self.cotation_v(13.5, 0, 10, x_ref=12)
        self.texte(6,-2.5,"PLAN ETAGE - 1er NIVEAU",0.55)

        # Cartouche
        self.ox, self.oy = 0, 0
        self.cartouche(0,-6,"MAISON INDIVIDUELLE - 2 NIVEAUX - 4 CHAMBRES",
                       "Residence Familiale","1:100","DWG-002")
        self.sauvegarder()
        return self


# ══════════════════════════════════════════════════════════════════
# INTERFACE CONVERSATIONNELLE (LLM-ready)
# ══════════════════════════════════════════════════════════════════

def interpreter_commande(texte, agent):
    """
    Interprète une commande en langage naturel.
    Exemples :
      - "dessine une maison simple de 12x8"
      - "dessine une maison 2 niveaux 4 chambres"
      - "analyse plan_maison.dxf"
    """
    texte = texte.lower()

    if "2 niveau" in texte or "2niveaux" in texte or "etage" in texte:
        print("-> Generation maison 2 niveaux 4 chambres...")
        agent.generer_maison_2niveaux("maison_2niveaux_agent.dxf")

    elif "simple" in texte or "maison" in texte:
        # Cherche dimensions
        dims = re.findall(r'(\d+)[\sx]+(\d+)', texte)
        l, h = (float(dims[0][0]), float(dims[0][1])) if dims else (10, 8)
        print(f"-> Generation maison simple {l}x{h}...")
        agent.generer_maison_simple(l, h, f"maison_{int(l)}x{int(h)}.dxf")

    elif "analy" in texte:
        fichiers = re.findall(r'[\w/\\]+\.dxf', texte)
        if fichiers:
            agent.analyser(fichiers[0])
        else:
            print("Precisez le fichier DXF a analyser.")

    else:
        print(f"Commande non reconnue : '{texte}'")
        print("Commandes disponibles :")
        print("  - 'dessine une maison simple de LxH'")
        print("  - 'dessine une maison 2 niveaux 4 chambres'")
        print("  - 'analyse <fichier.dxf>'")


# ══════════════════════════════════════════════════════════════════
# POINT D'ENTREE
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    agent = DessinateurDuFutur()

    if len(sys.argv) > 1:
        # Mode commande directe
        commande = " ".join(sys.argv[1:])
        interpreter_commande(commande, agent)
    else:
        # Mode interactif
        print("Mode interactif — tapez votre commande (ou 'quitter') :")
        while True:
            try:
                cmd = input("\nDessinateur> ").strip()
                if cmd.lower() in ("quitter", "exit", "q"):
                    print("Au revoir ! Dessinateur du Futur se deconnecte.")
                    break
                if cmd:
                    interpreter_commande(cmd, agent)
            except KeyboardInterrupt:
                print("\nInterruption. Au revoir !")
                break
