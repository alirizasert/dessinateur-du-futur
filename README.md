# Dessinateur du Futur — Agent AutoCAD IA

> L'agent IA qui dessine comme un architecte, pense comme une machine.

## Presentation

Dessinateur du Futur est un agent Python intelligent capable de :

- Generer des plans d'architecture complets (DXF/DWG)
- Analyser des fichiers AutoCAD existants
- Automatiser des taches dans AutoCAD (calques, couleurs, cartouches)
- Comprendre des commandes en langage naturel
- S'integrer avec des LLM (Claude, GPT-4) pour generer des plans a la demande

## Competences de l'agent

| Competence | Description |
|---|---|
| Plans architecturaux | Maison 1 ou 2 niveaux, appartements, bureaux |
| Calques professionnels | MURS, PORTES, FENETRES, COTES, TEXTES, ESCALIER, CARTOUCHE |
| Cotations automatiques | Dimensions horizontales et verticales |
| Cartouche complet | Titre, projet, echelle, dessinateur, date, revision |
| Langage naturel | Interprete des commandes comme "dessine une maison 2 niveaux" |
| Analyse DXF | Lit et rapporte le contenu de tout fichier DXF/DWG |

## Installation

```bash
pip install ezdxf pyautocad
git clone https://github.com/alirizasert/dessinateur-du-futur.git
cd dessinateur-du-futur
```

## Utilisation

### Mode interactif
```bash
python agent.py
```

```
Dessinateur> dessine une maison 2 niveaux 4 chambres
Dessinateur> dessine une maison simple de 12x8
Dessinateur> analyse plan_maison.dxf
Dessinateur> quitter
```

### Mode commande directe
```bash
python agent.py "dessine une maison 2 niveaux 4 chambres"
python agent.py "dessine une maison simple de 10x8"
```

### Mode Python
```python
from agent import DessinateurDuFutur

agent = DessinateurDuFutur()
agent.generer_maison_simple(largeur=12, hauteur=8, nom="ma_maison.dxf")
agent.generer_maison_2niveaux("maison_complete.dxf")
rapport = agent.analyser("plan_existant.dxf")
```

## Roadmap

- [ ] Integration API Claude/GPT pour generation par description
- [ ] Support des plans 3D
- [ ] Interface web (Flask/FastAPI)
- [ ] Plugin AutoCAD natif (AutoLISP)
- [ ] Exportation PDF automatique
- [ ] Reconnaissance de plans scannes (OCR vers DXF)

**Cree par alirizasert | Propulse par Claude AI | 2026**
