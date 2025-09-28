import argparse
import os
import requests
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime

SUGGESTIONS_FOLDER = "suggestions"
os.makedirs(SUGGESTIONS_FOLDER, exist_ok=True)

# --------------------------
# Wikipedia/Wikidata Check
# --------------------------
def check_wikipedia_multilang(taxon_names, languages=None):
    if languages is None:
        languages = ["en", "es", "ja", "th", "id", "cn", "de", "fr", "it", "ru", "pt", "ar", "ko", "nl"]

    verified = {}
    batch_size = 50

    for tn in taxon_names:
        verified[tn] = {"missing": languages[:], "existing": {}, "wikidata": False}

    lang_values = " ".join(f'("{l}" <https://{l}.wikipedia.org/>)' for l in languages)

    for chunks in [taxon_names[i:i + batch_size] for i in range(0, len(taxon_names), batch_size)]:
        names = " ".join(f'"{w}"' for w in chunks)
        query = f"""
        SELECT DISTINCT ?taxon_name ?lang ?article
        WHERE {{
            VALUES ?taxon_name {{ {names} }}
            VALUES (?lang ?wiki) {{ {lang_values} }}
            ?item wdt:P225 ?taxon_name .
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

            verified[tn]["wikidata"] = True
            if article:
                verified[tn]["existing"][lang] = article
                if lang in verified[tn]["missing"]:
                    verified[tn]["missing"].remove(lang)

    return verified

# --------------------------
# Fetch Taxon Names from iNaturalist
# --------------------------
def fetch_taxon_names_from_project(project_id):
    url = f"https://api.inaturalist.org/v1/observations?project_id={project_id}&per_page=200"
    response = requests.get(url)
    data = response.json()

    taxon_names = []
    species = []
    observers = []
    all_obs = []

    for obs in data.get("results", []):
        if "taxon" in obs and obs["taxon"]:
            name = obs["taxon"]["name"]
            taxon_names.append(name)
            species.append(name)
            observers.append(obs.get("user", {}).get("login", "Unknown"))
            all_obs.append(obs)

    return list(set(taxon_names)), species, observers, all_obs

# --------------------------
# Generate Markdown Report
# --------------------------
def generate_markdown_report(project_slug, languages=None):
    if languages is None:
        languages = ["en", "es", "ja", "th", "id"]

    taxon_names, species, observers, all_obs = fetch_taxon_names_from_project(project_slug)
    species_counts = Counter(species)
    observer_counts = Counter(observers)
    wiki_map = check_wikipedia_multilang(taxon_names, languages)

    md_lines = []
    md_lines.append(f"# iNaturalist Project Report: {project_slug}\n")
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
        plot_path = os.path.join(SUGGESTIONS_FOLDER, f"top_species_{project_slug}.png")
        plt.savefig(plot_path)
        plt.close()
        md_lines.append(f"![Top 10 Species]({plot_path})\n")

    if observer_counts:
        obs_labels, obs_values = zip(*observer_counts.most_common(10))
        plt.figure(figsize=(8, 5))
        plt.barh(obs_labels[::-1], obs_values[::-1])
        plt.xlabel("Number of observations")
        plt.title("Top 10 Most Active Observers")
        plt.tight_layout()
        plot_path = os.path.join(SUGGESTIONS_FOLDER, f"top_observers_{project_slug}.png")
        plt.savefig(plot_path)
        plt.close()
        md_lines.append(f"![Top 10 Observers]({plot_path})\n")

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

        # --- Table ---
        sorted_species = sorted(
            wiki_map.items(),
            key=lambda kv: (not kv[1]["wikidata"], -len(kv[1]["missing"]), kv[0].lower())
        )

        header = "| Species | Wikidata | " + " | ".join(languages) + " |\n"
        header += "|---|---|" + "|".join(["---"] * len(languages)) + "|\n"
        rows = []
        totals = {lang: 0 for lang in languages}

        for tn, langs in sorted_species:
            wd_status = "✅" if langs["wikidata"] else "⚠️"
            row = [tn, wd_status]
            for lang in languages:
                if lang in langs["existing"]:
                    row.append(f"[✅]({langs['existing'][lang]})")
                else:
                    row.append("❌")
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
    report_path = os.path.join(SUGGESTIONS_FOLDER, f"missing_wikipedia_project_{project_slug}_{timestamp}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"✅ Markdown report saved at: {report_path}")
    return report_path

# --------------------------
# CLI
# --------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="iNaturalist Wikipedia coverage report")
    parser.add_argument("project_id", type=str, help="iNaturalist Project ID")
    parser.add_argument("--languages", type=str, help="Comma-separated list of Wikipedia languages")
    args = parser.parse_args()

    langs = args.languages.split(",") if args.languages else None
    generate_markdown_report(args.project_id, languages=langs)
