"""
Script 3 : Automatiser des tâches dans AutoCAD
Deux méthodes :
  A) Via ezdxf (sans AutoCAD ouvert - modification de fichiers DXF)
  B) Via pyautocad (AutoCAD doit être ouvert - contrôle COM Windows)

Installation :
  pip install ezdxf pyautocad
"""

# ════════════════════════════════════════════════════════════
# MÉTHODE A : Automatisation via ezdxf (sans AutoCAD ouvert)
# ════════════════════════════════════════════════════════════

import ezdxf

def tache_renommer_calques(fichier_entree, fichier_sortie):
    """Renommer tous les calques d'un fichier DXF"""
    doc = ezdxf.readfile(fichier_entree)

    correspondance = {
        "Layer1": "MURS",
        "Layer2": "PORTES",
        "Layer3": "FENETRES",
        "0":      "DEFAULT",
    }

    for ancien, nouveau in correspondance.items():
        if ancien in doc.layers:
            calque = doc.layers.get(ancien)
            calque.dxf.name = nouveau
            print(f"Renommé : {ancien} → {nouveau}")

    doc.saveas(fichier_sortie)
    print(f"Fichier sauvegardé : {fichier_sortie}")


def tache_changer_couleurs(fichier_entree, fichier_sortie):
    """Changer les couleurs de tous les calques"""
    doc = ezdxf.readfile(fichier_entree)

    couleurs = {
        "MURS":     7,   # blanc
        "PORTES":   1,   # rouge
        "FENETRES": 4,   # cyan
        "COTES":    3,   # vert
        "TEXTES":   2,   # jaune
    }

    for nom_calque, couleur in couleurs.items():
        if nom_calque in doc.layers:
            doc.layers.get(nom_calque).dxf.color = couleur
            print(f"Calque '{nom_calque}' → couleur {couleur}")

    doc.saveas(fichier_sortie)


def tache_dupliquer_plan(fichier_entree, fichier_sortie, nb_copies=3, espacement=15):
    """Dupliquer un plan en grille (ex: plusieurs appartements)"""
    doc = ezdxf.readfile(fichier_entree)
    msp = doc.modelspace()

    entites_originales = list(msp)

    for i in range(1, nb_copies):
        decalage_x = i * espacement
        for entite in entites_originales:
            try:
                copie = entite.copy()
                if copie is not None:
                    msp.add_entity(copie)
                    copie.translate(decalage_x, 0, 0)
            except Exception:
                pass
        print(f"Copie {i} créée à X+{decalage_x}")

    doc.saveas(fichier_sortie)
    print(f"Plan dupliqué {nb_copies} fois → {fichier_sortie}")


def tache_ajouter_cartouche(fichier_entree, fichier_sortie, infos):
    """Ajouter un cartouche (bloc de titre) au plan"""
    doc = ezdxf.readfile(fichier_entree)
    msp = doc.modelspace()

    from ezdxf.enums import TextEntityAlignment

    x, y = infos.get("position", (12, -4))

    # Cadre du cartouche
    msp.add_lwpolyline(
        [(x, y), (x+10, y), (x+10, y+5), (x, y+5), (x, y)],
        dxfattribs={"layer": "0", "closed": True}
    )

    # Lignes de séparation
    msp.add_line((x, y+3.5), (x+10, y+3.5), dxfattribs={"layer": "0"})
    msp.add_line((x+5, y),   (x+5, y+3.5),  dxfattribs={"layer": "0"})

    # Textes
    champs = [
        (x+5,   y+4.3, infos.get("titre", "PLAN SANS TITRE"), 0.4),
        (x+2.5, y+2.5, infos.get("projet", "Projet"),         0.25),
        (x+7.5, y+2.5, infos.get("echelle", "1:100"),         0.25),
        (x+2.5, y+1.5, infos.get("dessinateur", "Auteur"),    0.2),
        (x+7.5, y+1.5, infos.get("date", "2026-05-17"),       0.2),
        (x+2.5, y+0.5, infos.get("revision", "Rev. 01"),      0.2),
        (x+7.5, y+0.5, infos.get("numero", "DWG-001"),        0.2),
    ]

    for cx, cy, texte, hauteur in champs:
        msp.add_text(
            texte,
            dxfattribs={"height": hauteur, "layer": "TEXTES"}
        ).set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)

    doc.saveas(fichier_sortie)
    print(f"Cartouche ajouté → {fichier_sortie}")


# ════════════════════════════════════════════════════════════
# MÉTHODE B : Contrôle direct d'AutoCAD ouvert (Windows COM)
# ════════════════════════════════════════════════════════════

def autocad_direct():
    """
    Contrôle AutoCAD directement (AutoCAD doit être ouvert)
    Nécessite : pip install pyautocad
    Fonctionne uniquement sur Windows avec AutoCAD installé
    """
    try:
        from pyautocad import Autocad, APoint

        acad = Autocad(create_if_not_exists=True)
        print(f"AutoCAD connecté : {acad.doc.Name}")

        msp = acad.model

        # Dessiner une ligne
        p1 = APoint(0, 0)
        p2 = APoint(100, 0)
        ligne = msp.AddLine(p1, p2)
        print(f"Ligne créée : {ligne}")

        # Dessiner un cercle
        centre = APoint(50, 50)
        cercle = msp.AddCircle(centre, 25)
        print(f"Cercle créé : {cercle}")

        # Ajouter du texte
        texte = msp.AddText("TEST AUTOCAD", APoint(10, 10), 5)
        print(f"Texte ajouté : {texte}")

        # Zoomer sur tout
        acad.app.ZoomExtents()

        print("Commandes exécutées dans AutoCAD !")

    except ImportError:
        print("pyautocad non installé. Exécutez : pip install pyautocad")
    except Exception as e:
        print(f"Erreur AutoCAD COM : {e}")
        print("Assurez-vous qu'AutoCAD est ouvert et en cours d'exécution.")


# ════════════════════════════════════════════════════════════
# PROGRAMME PRINCIPAL
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import os

    fichier = "plan_maison.dxf"

    if not os.path.exists(fichier):
        print("Fichier de base introuvable. Lancez d'abord 1_generer_plan.py")
    else:
        print("=== AUTOMATISATION DXF ===\n")

        # 1. Changer les couleurs
        tache_changer_couleurs(fichier, "plan_couleurs.dxf")

        # 2. Dupliquer le plan (3 copies)
        tache_dupliquer_plan(fichier, "plan_dupliquer.dxf", nb_copies=3)

        # 3. Ajouter un cartouche
        tache_ajouter_cartouche(fichier, "plan_cartouche.dxf", infos={
            "titre":       "PLAN RDC - MAISON",
            "projet":      "Residence Les Pins",
            "echelle":     "1:100",
            "dessinateur": "PC",
            "date":        "2026-05-17",
            "revision":    "Rev. 01",
            "numero":      "DWG-001",
        })

        print("\n✅ Toutes les tâches terminées !")

        # 4. Décommenter pour contrôle direct AutoCAD
        # autocad_direct()
