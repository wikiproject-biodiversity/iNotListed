import argparse
import json
import requests
import os
import sys
from datetime import datetime
from tqdm import tqdm
import time

# Ensure required dependencies are installed
try:
    from wikidataintegrator import wdi_core
except ImportError:
    print("Installing missing dependencies...")
    os.system("pip install wikidataintegrator tqdm")
    from wikidataintegrator import wdi_core

# Create suggestions folder if it doesn't exist
SUGGESTIONS_FOLDER = "suggestions"
os.makedirs(SUGGESTIONS_FOLDER, exist_ok=True)

def safe_request(url, max_retries=5):
    """Make API requests safely, handling rate limits (HTTP 429)."""
    retries = 0
    while retries < max_retries:
        response = requests.get(url)

        if response.status_code == 200:
            return response  # ✅ Successful response

        elif response.status_code == 429:  # Too many requests
            retry_after = int(response.headers.get("Retry-After", 20))  # Default: wait 10 sec
            print(f"⚠️ Rate limit reached! Waiting {retry_after} seconds before retrying...")
            time.sleep(retry_after)
            retries += 1  # Count the retry

        else:
            print(f"❌ Error fetching {url}: HTTP {response.status_code}")
            return None  # Stop on other errors

    print("❌ Max retries reached. Skipping this request.")
    return None  # Skip if too many failures

def fetch_missing_wikipedia_articles(base_url, args):
    """Fetch all pages of taxa from iNaturalist that are missing Wikipedia articles."""
    temp_results = []
    page = 1
    total_results = None

    print(f"Fetching data from iNaturalist: {base_url}")
    seen = []
    with tqdm(desc="Fetching iNaturalist pages", unit="page") as progress_bar:
        while True:
            url = f"{base_url}&page={page}"
            response = safe_request(url)

            if response.status_code != 200:
                print(f"Error fetching page {page}: {response.status_code}")
                break

            photos = response.json()

            if total_results is None:
                total_results = photos.get("total_results", 0)
                progress_bar.total = (total_results // 200) + 1

            for obs in photos.get("results", []):
                if len(obs["taxon"]["name"].split(" ")) == 2 and obs["taxon"]["wikipedia_url"] is None:
                    if obs["taxon"]["name"] not in seen:
                        seen.append(obs["taxon"]["name"])
                        temp_results.append({
                            "inat_obs_id": obs["id"],
                            "inat_taxon_id": obs["taxon"]["id"],
                            "taxon_name": obs["taxon"]["name"],
                        })

            progress_bar.update(1)

            if "results" not in photos or len(photos["results"]) < 200:
                break

            page += 1

    print(f"Total taxa fetched: "+str(page*200))

    return temp_results


def generate_markdown_report(missing_wikipedia_articles, search_type, search_value, args):
    """Generate a Markdown report with an index and multiple images per species."""

    # Define the filename dynamically based on search type
    filename = f"missing_wikipedia_{search_type}_{search_value}.md"
    report_path = os.path.join(SUGGESTIONS_FOLDER, filename)

    markdown_content = f"# 📖 Missing Wikipedia Articles Report ({search_type}: {search_value})\n\n"

    # Create an index at the top
    markdown_content += "## 📌 Index\n\n"

    for taxon in missing_wikipedia_articles:
        taxon_name = taxon["taxon_name"]
        markdown_content += f"- [{taxon_name}](#{taxon_name.replace(' ', '-').lower()})\n"

    markdown_content += "\n---\n\n"

    for taxon in missing_wikipedia_articles:
        taxon_name = taxon["taxon_name"]
        inat_id = taxon["inat_taxon_id"]

        markdown_content += f"## 🦠 {taxon_name}\n\n"
        markdown_content += f"🔗 **iNaturalist Page**: [View on iNaturalist](https://www.inaturalist.org/taxa/{inat_id})\n\n"

        # Fetch iNaturalist observations for the species
        # Fetch iNaturalist observations for the species
        obs_url = f"https://api.inaturalist.org/v1/observations?taxon_id={inat_id}&quality_grade=research&per_page=200"
        if hasattr(args, "username"):
            obs_url += f"&user_id={args.username}"
        if hasattr(args, "country_code"):
            obs_url += f"&place_id={args.country_code}"
        if hasattr(args, "project_id"):
            obs_url += f"&project_id={args.project_id}"
        print(obs_url)
        obs_response = safe_request(obs_url)

        images = []
        if obs_response:
            obs_data = obs_response.json()
            for obs in obs_data.get("results", []):
                if "photos" in obs and obs["photos"]:
                    for photo in obs["photos"]:
                        if "url" in photo:
                            images.append({
                                "url": photo.get("medium_url", photo["url"]),  # ✅ Fallback to another URL
                                "attribution": photo.get("attribution", "Unknown")
                            })

        # Add all images found
        if images:
            for img in images:
                markdown_content += f"![{taxon_name}]({img['url']})\n\n"
                markdown_content += f"📷 *Image credit*: {img['attribution']}\n\n"
        else:
            markdown_content += "❌ *No images available from observations.*\n\n"

        # Add BHL Reference
        bhl_url = f"https://www.biodiversitylibrary.org/name/{taxon_name.replace(' ', '_')}"
        markdown_content += f"### 📚 Biodiversity Heritage Library (BHL)\n"
        markdown_content += f"🔗 **BHL Page**: [View on BHL]({bhl_url})\n\n"

        # Add Wikimedia Commons
        commons_page = f"https://commons.wikimedia.org/wiki/Category:{taxon_name.replace(' ', '_')}"
        markdown_content += f"### 🖼 Wikimedia Commons\n"
        markdown_content += f"🔗 **Commons Category**: [View on Commons]({commons_page})\n\n"

        markdown_content += "---\n\n"

    # Save the Markdown file
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"✅ Markdown report saved in: {report_path}")

    # Save the Markdown file
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"✅ Markdown report saved in: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Find missing Wikipedia articles for taxa.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Taxon command
    taxon_parser = subparsers.add_parser("taxon", help="Search by taxon ID")
    taxon_parser.add_argument("taxon_id", type=int, help="iNaturalist Taxon ID")

    # User command
    user_parser = subparsers.add_parser("user", help="Search by user")
    user_parser.add_argument("username", help="iNaturalist Username")
    user_parser.add_argument("--wikipedia", default="https://en.wikipedia.org/", help="Wikipedia language version")

    # Country command
    country_parser = subparsers.add_parser("country", help="Search by country")
    country_parser.add_argument("country_code", type=int, help="iNaturalist Country Code")

    # Project command
    project_parser = subparsers.add_parser("project", help="Search by project")
    project_parser.add_argument("project_id", help="iNaturalist Project ID")
    project_parser.add_argument("--wikipedia", default="https://en.wikipedia.org/", help="Wikipedia language version")

    args = parser.parse_args()

    base_url = None
    search_type = None
    search_value = None  # ✅ Define these before using them

    if args.command == "taxon":
        base_url = f"https://api.inaturalist.org/v1/observations?taxon_id={args.taxon_id}&quality_grade=research&per_page=200"
        search_type = "taxon"
        search_value = args.taxon_id
    elif args.command == "user":
        base_url = f"https://api.inaturalist.org/v1/observations?user_id={args.username}&quality_grade=research&per_page=200"
        search_type = "user"
        search_value = args.username
    elif args.command == "country":
        base_url = f"https://api.inaturalist.org/v1/observations?place_id={args.country_code}&quality_grade=research&per_page=200"
        search_type = "country"
        search_value = args.country_code
    elif args.command == "project":
        base_url = f"https://api.inaturalist.org/v1/observations?project_id={args.project_id}&quality_grade=research&per_page=200"
        search_type = "project"
        search_value = args.project_id

    if base_url:
        results = fetch_missing_wikipedia_articles(base_url, args)
        if results:
            generate_markdown_report(results, search_type, search_value, args)  # ✅ Now properly defined!

if __name__ == "__main__":
    main()