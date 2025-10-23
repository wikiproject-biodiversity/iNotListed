# iNotWiki: Missing Wikipedia Articles CLI Tool

A command-line tool to find **missing Wikipedia articles** for biological taxa using **iNaturalist** and **Wikidata**.

## Features:
* Fetches observations from **iNaturalist** (with **pagination** support).  
* Checks **Wikidata** to see if taxa have existing **Wikipedia pages**.  
* Outputs a list of **taxa** that do **not** have Wikipedia articles.  
* Uses a **progress bar (`tqdm`)** to track both **iNaturalist pagination** and **Wikidata verification**.  
* Works via **CLI**, allowing searches by **taxon, user, country, or project**.  

---

## 📥 Installation
### **1. Install Python Dependencies**
You need **Python 3.7+**. Install required packages:
```sh
pip install requests tqdm wikidataintegrator
```

### **2. Download the script**
[Download `iNotWiki.py`](sandbox:/mnt/data/iNotWiki.py)  
Or, copy the script from this repository.

---

## 🚀 Usage
Run the script from the terminal:
```sh
python iNotWiki.py [command] [options]
```

### **Commands**
| Command | Description |
|---------|------------|
| `taxon` | Search for missing Wikipedia articles by **iNaturalist Taxon ID** |
| `user` | Search by **iNaturalist username** (find missing taxa in their observations) |
| `country` | Search by **iNaturalist country code** (find missing taxa from a country) |
| `project` | Search by **iNaturalist project ID** |

---

## 🎯 Examples
### 🔍 **Find missing Wikipedia articles for a taxon**
```sh
python iNotWiki.py taxon 47222
```

### 🧑‍🔬 **Find missing articles for an iNaturalist user**
```sh
python iNotWiki.py user example_user --wikipedia https://en.wikipedia.org/
```

### 🌍 **Find missing taxa from a country**
```sh
python iNotWiki.py country 21
```

### 🏗 **Find missing Wikipedia articles in a project**
```sh
python iNotWiki.py project 54321
```

---

## 🛠 Development & Contributions
Feel free to contribute to `iNotWiki` by submitting pull requests or reporting issues.

---

## 📜 License
This script is open-source and available under the **MIT License**.

