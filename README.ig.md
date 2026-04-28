[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · [日本語](README.ja.md) · [മലയാളം](README.ml.md) · **Igbo** · [Dagbanli](README.dag.md)

# iNotWiki — ihe nyochaa edemede Wikipedia na-efu

> ⚠️ **Nsụgharị nke nọ na-emepe — achọrọ nyochaa site n'aka ndị na-asụ Igbo.**
> E ji AI mepụta nsụgharị Igbo a; okwu teknụzụ nwere ike ọ gaghị ezi.
> A na-anabata ndozi na ntinye aka site na ndị obodo —
> [meghee issue na Codeberg](https://codeberg.org/wikiproject-biodiversity/iNotListed/issues)
> ma ọ bụ dezie faịlụ a kpọmkwem.

Ngwa ọrụ command-line maka ịchọta **edemede Wikipedia na-efu** maka taxa
ndụ, site n'iji **iNaturalist** na **Wikidata**.

> **Nchekwa ugboro abụọ.** Ọrụ a ka eweputara n'ụlọ ọrụ git abụọ dị iche
> ka ọ nwee ike ịdịgide na-arụ ọrụ ma ọ bụrụ na otu n'ime ha akwụsị
> ma ọ bụ gbanwee usoro ya:
>
> - **Isi:** [codeberg.org/wikiproject-biodiversity/iNotListed](https://codeberg.org/wikiproject-biodiversity/iNotListed) — issues, PR na CI nọ ebe a.
> - **Mirror:** [github.com/wikiproject-biodiversity/iNotListed](https://github.com/wikiproject-biodiversity/iNotListed) — read-only, ka a na-emelite ya.

## Atụmatụ
- Na-ewere nleba anya site na **iNaturalist** na pagination `id_above`
  (na-arụ ọrụ maka ihe karịrị nleba anya 10 000).
- Na-ajụ **Wikidata** ma chọpụta ma taxon ọ bụla ọ̀ nwere edemede
  Wikipedia n'asụsụ ndị a chọrọ.
- Na-ewepụta akụkọ Markdown nwere tebụl maka taxon ọ bụla, na chart PNG
  nke top 10 species/observers.
- Na-akọwa onwe ya dị ka `iNotListed/<version>` ma na-anwagharị maka
  HTTP errors (429 / 5xx) site n'iji exponential backoff.

---

## Nrụnye
Achọrọ **Python 3.9+**.

```sh
pip install requests matplotlib
```

---

## Iji ya
```sh
python iNotWiki.py [options]
```

Tinye **otu** n'ime `--project_id`, `--username`, ma ọ bụ `--country_id`.
Ọ bụrụ na ọ dịghị nke a chọtara, ọrụ a ga-eji `biohackathon-2025`.

| Nhọrọ            | Nkọwa                                                              |
|------------------|---------------------------------------------------------------------|
| `--project_id`    | iNaturalist project ID ma ọ bụ slug (ọmụmaatụ `biohackathon-2025`) |
| `--username`      | Aha onye iji iNaturalist                                            |
| `--country_id`    | iNaturalist place ID                                                |
| `--languages`     | Koodu asụsụ Wikipedia kewara site na rikoma (ndabara: `en,es,ja,ar,nl,pt,fr`) |
| `--output-folder` | Folda ebe Markdown report na PNG ga-anọ (ndabara: `reports`)        |

Script a na-ebipụta ụzọ akụkọ Markdown na stdout:

```sh
REPORT_PATH=$(python iNotWiki.py --project_id biohackathon-2025)
```

Na Forgejo Actions, ọ na-edekwa `report_path=…` na `$GITHUB_OUTPUT`.

---

## Ihe atụ

```sh
# Project (slug ma ọ bụ ID nke nọmba)
python iNotWiki.py --project_id biohackathon-2025

# Onye, asụsụ ole na ole
python iNotWiki.py --username johndoe --languages en,nl,de

# Ebe / obodo
python iNotWiki.py --country_id 7088 --output-folder reports/colombia
```

---

## Ikikere
MIT.
