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
        plt.barh(sp_labels[::-
