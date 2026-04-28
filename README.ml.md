[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · [日本語](README.ja.md) · **മലയാളം** · [Igbo](README.ig.md) · [Dagbanli](README.dag.md)

# iNotWiki — വിക്കിപീഡിയയിൽ കാണാത്ത ലേഖനങ്ങൾ കണ്ടെത്താനുള്ള ഉപകരണം

> ⚠️ **കരട് വിവർത്തനം — സ്വദേശി ഭാഷാ പണ്ഡിതരുടെ പരിശോധന ആവശ്യമാണ്.**
> ഈ മലയാള വിവർത്തനം AI ഉപയോഗിച്ച് സൃഷ്ടിച്ചതാണ്; സാങ്കേതിക പദാവലി കൃത്യമല്ലാതിരിക്കാം.
> തിരുത്തലുകളും മെച്ചപ്പെടുത്തലുകളും സ്വാഗതം —
> [Codeberg-ൽ ഒരു issue തുറക്കുക](https://codeberg.org/wikiproject-biodiversity/iNotListed/issues)
> അല്ലെങ്കിൽ ഈ ഫയൽ നേരിട്ട് തിരുത്തുക.

**iNaturalist**, **Wikidata** എന്നിവ ഉപയോഗിച്ച് ജൈവ ടാക്സയ്ക്കായി
വിക്കിപീഡിയയിൽ ലഭ്യമല്ലാത്ത ലേഖനങ്ങൾ കണ്ടെത്താനുള്ള ഒരു command-line tool.

> **ഇരട്ട ഹോസ്റ്റിംഗ്.** ഒരു forge പ്രവർത്തനരഹിതമായാലോ നിബന്ധനകൾ
> മാറിയാലോ പ്രവേശനയോഗ്യമായി തുടരാൻ, ഈ പ്രോജക്ട് മനപ്പൂർവ്വം രണ്ട്
> സ്വതന്ത്ര forge-കളിൽ പ്രസിദ്ധീകരിച്ചിരിക്കുന്നു:
>
> - **പ്രാഥമികം:** [codeberg.org/wikiproject-biodiversity/iNotListed](https://codeberg.org/wikiproject-biodiversity/iNotListed) — issue, PR, CI ഇവിടെയാണ്.
> - **Mirror:** [github.com/wikiproject-biodiversity/iNotListed](https://github.com/wikiproject-biodiversity/iNotListed) — sync ചെയ്ത, read-only പകർപ്പ്.

## സവിശേഷതകൾ
- **iNaturalist**-ൽ നിന്ന് നിരീക്ഷണങ്ങൾ വീണ്ടെടുക്കുന്നു (`id_above` pagination
  ഉപയോഗിച്ച്, 10,000-ൽ കൂടുതൽ നിരീക്ഷണങ്ങളുള്ള പ്രോജക്റ്റുകൾക്കും പ്രവർത്തിക്കും).
- ആവശ്യപ്പെട്ട ഭാഷകളിൽ വിക്കിപീഡിയ ലേഖനങ്ങൾ ഉണ്ടോ എന്ന് **Wikidata**-യിൽ
  ഓരോ ടാക്സയും പരിശോധിക്കുന്നു.
- ഓരോ ടാക്സയ്ക്കും ഒരു പട്ടികയും, ഏറ്റവും കൂടുതൽ നിരീക്ഷിക്കപ്പെട്ട ജീവിവർഗ്ഗങ്ങളുടെയും
  സജീവ നിരീക്ഷകരുടെയും top-10 PNG charts ഉൾപ്പെടുന്ന ഒരു Markdown report സൃഷ്ടിക്കുന്നു.
- `iNotListed/<version>` എന്ന് സ്വയം തിരിച്ചറിയുന്നു; ക്ഷണിക HTTP errors
  (429 / 5xx) exponential backoff-ഓടെ വീണ്ടും ശ്രമിക്കുന്നു.

---

## ഇൻസ്റ്റാൾ ചെയ്യൽ
**Python 3.9+** ആവശ്യമാണ്.

```sh
pip install requests matplotlib
```

---

## ഉപയോഗം
```sh
python iNotWiki.py [options]
```

`--project_id`, `--username`, `--country_id` എന്നിവയിൽ **ഒന്ന് മാത്രം** നൽകുക.
ഒന്നും നൽകിയില്ലെങ്കിൽ `biohackathon-2025` പ്രോജക്റ്റ് സ്വീകരിക്കും.

| Option            | വിവരണം                                                          |
|-------------------|------------------------------------------------------------------|
| `--project_id`    | iNaturalist project ID അല്ലെങ്കിൽ slug (ഉദാ. `biohackathon-2025`) |
| `--username`      | iNaturalist username                                             |
| `--country_id`    | iNaturalist place ID                                             |
| `--languages`     | comma കൊണ്ട് വേർതിരിച്ച Wikipedia language codes (default: `en,es,ja,ar,nl,pt,fr`) |
| `--output-folder` | Markdown report-ഉം PNG-കളും save ചെയ്യാനുള്ള folder (default: `reports`) |

Script generated Markdown report-ന്റെ path stdout-ൽ print ചെയ്യുന്നു:

```sh
REPORT_PATH=$(python iNotWiki.py --project_id biohackathon-2025)
```

Forgejo Actions-ൽ run ചെയ്യുമ്പോൾ `report_path=…` എന്നത് `$GITHUB_OUTPUT`-ലും എഴുതും.

---

## ഉദാഹരണങ്ങൾ

```sh
# Project (slug അല്ലെങ്കിൽ numeric ID)
python iNotWiki.py --project_id biohackathon-2025

# User, ചില ഭാഷകൾ മാത്രം
python iNotWiki.py --username johndoe --languages en,nl,de

# Place / country
python iNotWiki.py --country_id 7088 --output-folder reports/colombia
```

---

## License
MIT.
