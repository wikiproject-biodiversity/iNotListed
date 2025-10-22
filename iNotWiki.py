import argparse
import os
import requests
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime

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
    print(lang_values)

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
        r = requests.get(url, params={"format": "json", "query": query})
        if not r.ok:
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
        "page": 1
    }

    if search_type == "project":
        params["project_id"] = search_value
    elif search_type == "user":
        params["user_id"] = search_value
    elif search_type == "country":
        params["place_id"] = search_value
    else:
        raise ValueError("Invalid search_type")

    taxon_names = []
    species = []
    observers = []
    all_obs = []

    while True:
        print(f"Fetching page {params['page']}...")
        response = requests.get(base_url, params=params)
        if not response.ok:
            print(f"Error fetching page {params['page']}: {response.status_code}")
            break

        data = response.json()
        results = data.get("results", [])
        if not results:
            break  # stop when no more results

        for obs in results:
            if "taxon" in obs and obs["taxon"]:
                name = obs["taxon"]["name"]
                taxon_names.append(name)
                species.append(name)
                observers.append(obs.get("user", {}).get("login", "Unknown"))
                all_obs.append(obs)

        if len(results) < 200:
            break  # last page reached
        params["page"] += 1

    print(f"Fetched total {len(all_obs)} observations across {params['page']} pages.")
    return list(set(taxon_names)), species, observers, all_obs
    
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
    if wiki_map:
        missing_counts = Counter()
        not_on_wd = 0
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
            wd_link = f"[{langs_info['wikidata_uri']}]({langs_info['wikidata_uri']})" if langs_info["wikidata_uri"] else "—"
            gbif_link = f"[{langs_info['gbif_uri']}]({langs_info['gbif_uri']})" if langs_info["gbif_uri"] else "—"
            inat_link = f"[{langs_info['inaturalist_uri']}]({langs_info['inaturalist_uri']})" if langs_info["inaturalist_uri"] else "—"
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
    return report_path

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
        report_path = generate_markdown_report(args.username, search_type="user", languages=langs, output_folder=args.output_folder)
    elif args.project_id:
        report_path = generate_markdown_report(args.project_id, search_type="project", languages=langs, output_folder=args.output_folder)
    elif args.country_id:
        report_path = generate_markdown_report(args.country_id, search_type="country", languages=langs, output_folder=args.output_folder)
    else:
        DEFAULT_PROJECT_ID = "biohackathon-2025"
        report_path = generate_markdown_report(DEFAULT_PROJECT_ID, search_type="project", languages=langs, output_folder=args.output_folder)

    print(f"REPORT_PATH={report_path}")
