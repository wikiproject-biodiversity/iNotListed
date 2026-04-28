import argparse
import sys
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime

USER_AGENT = "iNotListed/0.2 (+https://github.com/wikiproject-biodiversity/iNotListed)"


def _build_session():
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    retry = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


SESSION = _build_session()

# --------------------------
# Wikipedia/Wikidata Check
# --------------------------
def check_wikipedia_multilang(taxon_names, languages=None):
    if languages is None:
        languages = ["en", "es", "ja", "ar", "nl", "pt", "fr"]

    verified = {}
    batch_size = 50

    for tn in taxon_names:
        verified[tn] = {
            "missing": languages[:],
            "existing": {},
            "wikidata": False,
            "wikidata_uri": None,
            "gbif_uri": None,
            "inaturalist_uri": None
        }

    lang_values = " ".join(f'("{l}" <https://{l}.wikipedia.org/>)' for l in languages)

    for chunks in [taxon_names[i:i + batch_size] for i in range(0, len(taxon_names), batch_size)]:
        names = " ".join(f'"{w}"' for w in chunks)

        query = f"""
        SELECT DISTINCT ?item ?itemURI ?taxon_name ?lang ?article ?iNaturalist_URI ?gbif_URI
        WHERE {{
            VALUES ?taxon_name {{ {names} }}
            VALUES (?lang ?wiki) {{ {lang_values} }}

            ?item wdt:P225 ?taxon_name .
            BIND(IRI(CONCAT("https://www.wikidata.org/entity/", STRAFTER(STR(?item), "entity/"))) AS ?itemURI)

            OPTIONAL {{
                ?item wdt:P3151 ?iNaturalist_taxon .
                BIND(IRI(CONCAT("https://www.inaturalist.org/taxa/", STR(?iNaturalist_taxon))) AS ?iNaturalist_URI)
            }}
            OPTIONAL {{
                ?item wdt:P846 ?gbif_taxon .
                BIND(IRI(CONCAT("https://www.gbif.org/species/", STR(?gbif_taxon))) AS ?gbif_URI)
            }}
            OPTIONAL {{
                ?article schema:about ?item ;
                         schema:isPartOf ?wiki .
            }}
        }}
        """

        url = "https://query.wikidata.org/sparql"
        try:
            r = SESSION.get(url, params={"format": "json", "query": query}, timeout=90)
        except requests.RequestException as exc:
            print(f"Wikidata SPARQL error for batch of {len(chunks)} taxa: {exc}", file=sys.stderr)
            continue
        if not r.ok:
            print(
                f"Wikidata SPARQL HTTP {r.status_code} for batch of {len(chunks)} taxa: "
                f"{r.text[:200]}",
                file=sys.stderr,
            )
            continue

        results = r.json()["results"]["bindings"]
        for res in results:
            tn = res["taxon_name"]["value"]
            lang = res["lang"]["value"]
            article = res.get("article", {}).get("value")
            wd_uri = res.get("itemURI", {}).get("value")
            gbif_uri = res.get("gbif_URI", {}).get("value")
            inat_uri = res.get("iNaturalist_URI", {}).get("value")

            if tn not in verified:
                verified[tn] = {
                    "missing": languages[:],
                    "existing": {},
                    "wikidata": False,
                    "wikidata_uri": None,
                    "gbif_uri": None,
                    "inaturalist_uri": None
                }

            verified[tn]["wikidata"] = True
            verified[tn]["wikidata_uri"] = wd_uri or verified[tn]["wikidata_uri"]
            verified[tn]["gbif_uri"] = gbif_uri or verified[tn]["gbif_uri"]
            verified[tn]["inaturalist_uri"] = inat_uri or verified[tn]["inaturalist_uri"]

            if article:
                verified[tn]["existing"][lang] = article
                if lang in verified[tn]["missing"]:
                    verified[tn]["missing"].remove(lang)

    return verified

# --------------------------
# Fetch Taxon Names from iNaturalist
# --------------------------
def fetch_taxon_names(search_type, search_value):
    base_url = "https://api.inaturalist.org/v1/observations"
    params = {
        "per_page": 200,
        "order": "asc",
        "order_by": "id",
        "id_above": 0,
    }

    if search_type == "project":
        params["project_id"] = search_value
    elif search_type == "user":
        params["user_id"] = search_value
    elif search_type == "country":
        params["place_id"] = search_value
    else:
        raise ValueError("Invalid search_type")

    species = []
    observers = []
    all_obs = []
    page_count = 0

    while True:
        page_count += 1
        print(f"Fetching iNaturalist page {page_count} (id_above={params['id_above']})...", file=sys.stderr)
        try:
            response = SESSION.get(base_url, params=params, timeout=60)
        except requests.RequestException as exc:
            print(f"iNaturalist request failed on page {page_count}: {exc}", file=sys.stderr)
            break
        if not response.ok:
            print(
                f"iNaturalist HTTP {response.status_code} on page {page_count}: "
                f"{response.text[:200]}",
                file=sys.stderr,
            )
            break

        data = response.json()
        results = data.get("results", [])
        if not results:
            break

        max_id = params["id_above"]
        for obs in results:
            obs_id = obs.get("id", 0)
            if obs_id > max_id:
                max_id = obs_id
            if "taxon" in obs and obs["taxon"]:
                name = obs["taxon"]["name"]
                species.append(name)
                observers.append(obs.get("user", {}).get("login", "Unknown"))
                all_obs.append(obs)

        if len(results) < params["per_page"]:
            break
        if max_id == params["id_above"]:
            break  # no progress, avoid infinite loop
        params["id_above"] = max_id

    unique_taxa = list(dict.fromkeys(species))  # preserve first-seen order
    print(
        f"Fetched {len(all_obs)} observations across {page_count} pages "
        f"({len(unique_taxa)} unique taxa).",
        file=sys.stderr,
    )
    return unique_taxa, species, observers, all_obs
    
# --------------------------
# Generate Markdown Report
# --------------------------
def generate_markdown_report(search_value, search_type="project", languages=None, output_folder="reports"):
    if languages is None:
        languages = ["en", "es", "ja", "ar", "nl", "pt", "fr"]

    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    taxon_names, species, observers, all_obs = fetch_taxon_names(search_type, search_value)
    species_counts = Counter(species)
    observer_counts = Counter(observers)
    wiki_map = check_wikipedia_multilang(taxon_names, languages)

    md_lines = []
    md_lines.append(f"# iNaturalist {search_type.capitalize()} Report: {search_value}\n")
    md_lines.append(f"- Total observations: {len(all_obs)}")
    md_lines.append(f"- Unique species observed: {len(set(species))}")
    md_lines.append(f"- Unique observers: {len(set(observers))}\n")

    # --- Plots ---
    if species_counts:
        sp_labels, sp_values = zip(*species_counts.most_common(10))
        plt.figure(figsize=(8, 5))
        plt.barh(sp_labels[::-1], sp_values[::-1])
        plt.xlabel("Number of observations")
        plt.title("Top 10 Most Observed Species")
        plt.tight_layout()
        sp_plot_path = os.path.join(output_folder, f"top_species_{search_value}.png")
        plt.savefig(sp_plot_path)
        plt.close()
        md_lines.append(f"![Top 10 Species]({os.path.basename(sp_plot_path)})\n")

    if observer_counts:
        obs_labels, obs_values = zip(*observer_counts.most_common(10))
        plt.figure(figsize=(8, 5))
        plt.barh(obs_labels[::-1], obs_values[::-1])
        plt.xlabel("Number of observations")
        plt.title("Top 10 Most Active Observers")
        plt.tight_layout()
        obs_plot_path = os.path.join(output_folder, f"top_observers_{search_value}.png")
        plt.savefig(obs_plot_path)
        plt.close()
        md_lines.append(f"![Top 10 Observers]({os.path.basename(obs_plot_path)})\n")

    # --- Wikipedia/Wikidata Coverage ---
    missing_counts: Counter = Counter()
    not_on_wd = 0
    if wiki_map:
        for tn, langs in wiki_map.items():
            if not langs["wikidata"]:
                not_on_wd += 1
            for lang in langs["missing"]:
                missing_counts[lang] += 1

        md_lines.append("## Wikipedia & Wikidata Coverage\n")
        md_lines.append(f"- Species not on Wikidata: **{not_on_wd}**")
        for lang in languages:
            md_lines.append(f"- Missing in {lang}: **{missing_counts[lang]}**\n")

        # Table header uses language codes explicitly
        header = "| Taxon | Wikidata | GBIF | iNaturalist | " + " | ".join([lang.upper() for lang in languages]) + " |\n"
        header += "|---|---|---|---|" + "|".join(["---"] * len(languages)) + "|"
        rows = []
        totals = {lang: 0 for lang in languages}

        for tn, langs_info in sorted(wiki_map.items(), key=lambda kv: (not kv[1]["wikidata"], -len(kv[1]["missing"]), kv[0].lower())):
            wd_status = "&#10003;" if langs_info["wikidata"] else "&#10007;"
            wd_link = f"[{langs_info['wikidata_uri'].rsplit('/', 1)[-1]}]({langs_info['wikidata_uri']})" if langs_info["wikidata_uri"] else "—"
            gbif_link = f"[{langs_info['gbif_uri'].rsplit('/', 1)[-1]}]({langs_info['gbif_uri']})" if langs_info["gbif_uri"] else "—"
            inat_link = f"[{langs_info['inaturalist_uri'].rsplit('/', 1)[-1]}]({langs_info['inaturalist_uri']})" if langs_info["inaturalist_uri"] else "—"
            row = [tn, wd_link, gbif_link, inat_link]
            for lang in languages:
                if lang in langs_info["existing"]:
                    # Show ✅ with link
                    row.append(f"[&#10003;]({langs_info['existing'][lang]})")
                else:
                    row.append("&#10007;")
                    totals[lang] += 1
            rows.append("| " + " | ".join(row) + " |")

        total_row = ["**Totals**", ""]
        for lang in languages:
            total_row.append(str(totals[lang]))
        rows.append("| " + " | ".join(total_row) + " |")
        md_lines.append("\n".join([header] + rows))
    else:
        md_lines.append("All species have Wikipedia articles in selected languages.\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"missing_wikipedia_{search_type}_{search_value}_{timestamp}.md"
    report_path = os.path.join(output_folder, report_filename)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    summary = {
        "search_type": search_type,
        "search_value": search_value,
        "languages": list(languages),
        "total_observations": len(all_obs),
        "unique_species": len(set(species)),
        "unique_observers": len(set(observers)),
        "not_on_wikidata": not_on_wd,
        "missing_by_lang": {lang: int(missing_counts.get(lang, 0)) for lang in languages},
        "top_species": species_counts.most_common(5),
        "top_observers": observer_counts.most_common(5),
    }
    return report_path, summary

# --------------------------
# CLI
# --------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="iNaturalist Wikipedia coverage report")
    parser.add_argument("--project_id", type=str, help="iNaturalist Project ID")
    parser.add_argument("--username", type=str, help="iNaturalist Username")
    parser.add_argument("--country_id", type=str, help="iNaturalist Country/Place ID")
    parser.add_argument("--languages", type=str, help="Comma-separated list of Wikipedia languages")
    parser.add_argument("--output-folder", type=str, default="reports", help="Folder to store markdown and plots")
    args = parser.parse_args()

    langs = args.languages.split(",") if args.languages else None

    if args.username:
        report_path, _ = generate_markdown_report(args.username, search_type="user", languages=langs, output_folder=args.output_folder)
    elif args.project_id:
        report_path, _ = generate_markdown_report(args.project_id, search_type="project", languages=langs, output_folder=args.output_folder)
    elif args.country_id:
        report_path, _ = generate_markdown_report(args.country_id, search_type="country", languages=langs, output_folder=args.output_folder)
    else:
        DEFAULT_PROJECT_ID = "biohackathon-2025"
        report_path, _ = generate_markdown_report(DEFAULT_PROJECT_ID, search_type="project", languages=langs, output_folder=args.output_folder)

    # Stdout = path only, so workflows can do REPORT_PATH=$(python iNotWiki.py …).
    print(report_path)
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write(f"report_path={report_path}\n")
