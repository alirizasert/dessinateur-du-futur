"""
Script 2 : Lire et analyser un fichier DWG/DXF existant
Bibliothèque : ezdxf
Installation : pip install ezdxf
"""

import ezdxf
from ezdxf.enums import TextEntityAlignment
import os

def analyser_fichier(chemin_fichier):
    print(f"\n{'='*50}")
    print(f"Analyse de : {chemin_fichier}")
    print(f"{'='*50}")

    try:
        doc = ezdxf.readfile(chemin_fichier)
    except Exception as e:
        print(f"Erreur de lecture : {e}")
        return

    msp = doc.modelspace()

    # ── Infos générales ───────────────────────────────────────
    print(f"\n📄 Version DXF  : {doc.dxfversion}")
    print(f"📐 Unités       : {doc.header.get('$INSUNITS', 'Non défini')}")

    # ── Calques ───────────────────────────────────────────────
    calques = list(doc.layers)
    print(f"\n📋 Calques ({len(calques)}) :")
    for calque in calques:
        print(f"   - {calque.dxf.name} | Couleur: {calque.dxf.color}")

    # ── Compter les entités ───────────────────────────────────
    compteur = {}
    for entite in msp:
        type_entite = entite.dxftype()
        compteur[type_entite] = compteur.get(type_entite, 0) + 1

    print(f"\n📊 Entités dans le plan :")
    for type_e, count in sorted(compteur.items()):
        print(f"   {type_e:<20} : {count}")

    # ── Extraire les lignes ───────────────────────────────────
    lignes = [e for e in msp if e.dxftype() == "LINE"]
    print(f"\n📏 Lignes ({len(lignes)}) - 5 premières :")
    for ligne in lignes[:5]:
        debut = ligne.dxf.start
        fin   = ligne.dxf.end
        longueur = ((fin.x - debut.x)**2 + (fin.y - debut.y)**2) ** 0.5
        print(f"   ({debut.x:.2f},{debut.y:.2f}) → ({fin.x:.2f},{fin.y:.2f}) | L={longueur:.2f}")

    # ── Extraire les textes ───────────────────────────────────
    textes = [e for e in msp if e.dxftype() in ("TEXT", "MTEXT")]
    if textes:
        print(f"\n📝 Textes ({len(textes)}) :")
        for t in textes[:10]:
            if t.dxftype() == "TEXT":
                print(f"   \"{t.dxf.text}\" @ ({t.dxf.insert.x:.1f},{t.dxf.insert.y:.1f})")
            else:
                print(f"   \"{t.plain_mtext()[:50]}\"")

    # ── Extraire les blocs ────────────────────────────────────
    blocs = [e for e in msp if e.dxftype() == "INSERT"]
    if blocs:
        print(f"\n🔷 Blocs insérés ({len(blocs)}) :")
        for b in blocs[:10]:
            print(f"   Bloc: {b.dxf.name} @ ({b.dxf.insert.x:.1f},{b.dxf.insert.y:.1f})")

    # ── Superficie approximative ──────────────────────────────
    rectangles = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
    if rectangles:
        print(f"\n📐 Polylignes fermées : {len(rectangles)}")

    print(f"\n✅ Analyse terminée !")

def lister_calque(chemin_fichier, nom_calque):
    """Extraire toutes les entités d'un calque spécifique"""
    doc = ezdxf.readfile(chemin_fichier)
    msp = doc.modelspace()

    print(f"\nEntités sur le calque '{nom_calque}' :")
    for entite in msp.query(f'* [layer=="{nom_calque}"]'):
        print(f"  {entite.dxftype()} | {entite.dxf.all_existing_dxf_attribs()}")

if __name__ == "__main__":
    # Exemple d'utilisation
    fichier = "plan_maison.dxf"  # Remplacez par votre fichier

    if os.path.exists(fichier):
        analyser_fichier(fichier)
        # lister_calque(fichier, "MURS")  # décommenter pour filtrer par calque
    else:
        print(f"Fichier '{fichier}' introuvable.")
        print("Générez d'abord un plan avec le script 1_generer_plan.py")
