[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · [日本語](README.ja.md) · [മലയാളം](README.ml.md) · [Igbo](README.ig.md) · **Dagbanli**

# iNotWiki — Wikipedia lahabaya din ka nya

> ⚠️ **Lahabali din kpaŋsi — Dagbanli yɛliŋ tira sani.**
> Bɛ ti niŋ Dagbanli lahabali ŋɔ ni AI. Di mali yɛla shɛŋa din ku ti palli niŋ.
> Ti deei tilɔɣu mini sɔŋsim Dagbanli yɛltɔɣa puuni —
> [neei issue Codeberg zuɣu](https://codeberg.org/wikiproject-biodiversity/iNotListed/issues)
> bee n-ŋmaai fail ŋɔ.

Command-line tool din nyɛla ka nyari **Wikipedia lahabaya din ka nya**
biological taxa zuɣu, ka di tumdi tuma ni **iNaturalist** mini **Wikidata**.

> **Hosting bunyɛla niŋ buyi.** Bɛ tibi ŋɔ niŋ git forge buyi din pa taba zuɣu
> domin di nyɛŋ tum tuma yɛla yi shɛli ti zaŋ:
>
> - **Pun:** [codeberg.org/wikiproject-biodiversity/iNotListed](https://codeberg.org/wikiproject-biodiversity/iNotListed) — issues, PR ni CI ti be kpe.
> - **Mirror:** [github.com/wikiproject-biodiversity/iNotListed](https://github.com/wikiproject-biodiversity/iNotListed) — read-only, di tooi tum.

## Yɛltɔɣa
- Di mali iNaturalist sani niŋ pagination ni `id_above` (di tumdi nleba anya
  10 000 zuɣupiɛlim).
- Di nyari taxon ŋɔ Wikidata zuɣu, ka nyari Wikipedia lahabaya yɛltɔɣa shɛŋa
  ŋɔ.
- Di ti generate Markdown report din mali table taxon ŋɔ zuɣu, ni PNG charts
  top 10 species/observers.
- Di kpɛhi `iNotListed/<version>` ka di tooi try HTTP errors (429 / 5xx)
  niŋ exponential backoff.

---

## Installation
**Python 3.9+** ti yi.

```sh
pip install requests matplotlib
```

---

## Tum tuma
```sh
python iNotWiki.py [options]
```

Tibi **yini** n-ti `--project_id`, `--username`, bee `--country_id`.
Yi yi pa tibi shɛli, di yi tumdi `biohackathon-2025`.

| Option            | Yɛltɔɣa                                                            |
|-------------------|---------------------------------------------------------------------|
| `--project_id`    | iNaturalist project ID bee slug (m.b., `biohackathon-2025`)         |
| `--username`      | iNaturalist username                                                |
| `--country_id`    | iNaturalist place ID                                                |
| `--languages`     | Wikipedia language codes (default: `en,es,ja,ar,nl,pt,fr`)          |
| `--output-folder` | Folder din mali Markdown report ni PNG (default: `reports`)         |

Script ŋɔ pun report path stdout zuɣu:

```sh
REPORT_PATH=$(python iNotWiki.py --project_id biohackathon-2025)
```

Forgejo Actions puuni, di mali `report_path=…` `$GITHUB_OUTPUT` zuɣu.

---

## Misalan

```sh
# Project (slug bee numeric ID)
python iNotWiki.py --project_id biohackathon-2025

# User, languages shɛŋa
python iNotWiki.py --username johndoe --languages en,nl,de

# Place / country
python iNotWiki.py --country_id 7088 --output-folder reports/colombia
```

---

## License
MIT.
