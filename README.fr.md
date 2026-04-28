[English](README.md) · **Français** · [Español](README.es.md) · [日本語](README.ja.md) · [മലയാളം](README.ml.md) · [Igbo](README.ig.md) · [Dagbanli](README.dag.md)

# iNotWiki — articles Wikipédia manquants

> 🌍 *Cette traduction française a été produite avec l'aide d'une IA.
> Les contributions et relectures de la communauté sont les bienvenues —
> [ouvrez un ticket sur Codeberg](https://codeberg.org/wikiproject-biodiversity/iNotListed/issues)
> ou modifiez directement ce fichier.*

Outil en ligne de commande pour repérer les **articles Wikipédia manquants**
pour des taxons biologiques, à partir d'**iNaturalist** et **Wikidata**.

> **Hébergement redondant.** Ce projet est volontairement publié sur deux
> forges indépendantes pour rester accessible si l'une devient indisponible
> ou modifie ses conditions :
>
> - **Source principale :** [codeberg.org/wikiproject-biodiversity/iNotListed](https://codeberg.org/wikiproject-biodiversity/iNotListed) — issues, PR et CI.
> - **Miroir :** [github.com/wikiproject-biodiversity/iNotListed](https://github.com/wikiproject-biodiversity/iNotListed) — synchronisé en lecture seule.

## Fonctionnalités
- Récupère les observations depuis **iNaturalist** avec une pagination
  via `id_above` (fonctionne au-delà de 10 000 observations).
- Interroge **Wikidata** pour vérifier l'existence d'articles Wikipédia
  dans les langues demandées.
- Génère un rapport Markdown avec un tableau par taxon et des graphiques PNG
  des espèces les plus observées et des observateurs les plus actifs.
- S'identifie comme `iNotListed/<version>` et réessaie automatiquement les
  erreurs HTTP transitoires (429 / 5xx) avec un *backoff* exponentiel.

---

## Installation
Nécessite **Python 3.9+**.

```sh
pip install requests matplotlib
```

---

## Utilisation
```sh
python iNotWiki.py [options]
```

Fournissez exactement **un** des arguments `--project_id`, `--username`
ou `--country_id`. À défaut, le projet `biohackathon-2025` est utilisé.

| Option            | Description                                                       |
|-------------------|-------------------------------------------------------------------|
| `--project_id`    | Identifiant ou slug d'un projet iNaturalist (ex. `biohackathon-2025`) |
| `--username`      | Nom d'utilisateur iNaturalist                                     |
| `--country_id`    | Identifiant de lieu iNaturalist                                   |
| `--languages`     | Codes de langues Wikipédia, séparés par virgule (par défaut : `en,es,ja,ar,nl,pt,fr`) |
| `--output-folder` | Dossier de sortie pour le rapport Markdown et les PNG (par défaut : `reports`) |

Le script affiche le chemin du rapport Markdown sur stdout pour faciliter
la capture en shell :

```sh
REPORT_PATH=$(python iNotWiki.py --project_id biohackathon-2025)
```

Sous Forgejo Actions, il écrit également `report_path=…` dans `$GITHUB_OUTPUT`.

---

## Exemples

```sh
# Projet (slug ou ID numérique)
python iNotWiki.py --project_id biohackathon-2025

# Utilisateur, restreint à quelques langues
python iNotWiki.py --username johndoe --languages en,nl,de

# Lieu / pays
python iNotWiki.py --country_id 7088 --output-folder reports/colombia
```

---

## Interface par tickets (Codeberg / Forgejo Actions)
Deux modèles de tickets déclenchent les workflows dans `.forgejo/workflows/` :

- **`[Wikiblitz]: …`** — exécute le workflow « projet uniquement ».
- **`[Missing Wikipedia]: …`** — formulaire complet (projet / utilisateur /
  pays + cases à cocher pour les langues).

Les deux workflows enregistrent le rapport généré sous `reports/issue-<n>/`
puis publient (une copie tronquée du) Markdown en commentaire du ticket.

---

## Développement
Pour l'instant, l'outil tient dans un seul fichier (`iNotWiki.py`).
Un petit bot Telegram qui l'enveloppe est en cours de développement —
voir le suivi de tickets.

## Licence
MIT.
