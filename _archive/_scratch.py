import os
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from scrape_Tamarack import scrape_Tamarack

def extract_bandcamp_info(band_name):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)

    search_url = f"https://bandcamp.com/search?q={band_name.replace(' ', '+')}&item_type=b"
    driver.get(search_url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    result = soup.find("li", class_="searchresult data-search")

    info = {
        "band": band_name,
        "bandcamp_url": None,
        "location": None,
        "genre": None,
        "tags": [],
        "band_image": None,
    }

    if result:
        # location
        subhead = result.find("div", class_="subhead")
        info["location"] = subhead.text.strip() if subhead else None

        # URL
        itemurl = result.find("a", class_="artcont")
        raw_url = itemurl['href'] if itemurl else ""
        match = re.search(r"(https://[a-z0-9\-]+\.bandcamp\.com)", raw_url)
        info["bandcamp_url"] = match.group(1) if match else raw_url.split('?')[0]

        # genre
        genre_tag = result.find("div", class_="genre")
        info["genre"] = genre_tag.text.replace("genre:", "").strip() if genre_tag else None

        # tags
        tags_div = result.find("div", class_="tags")
        if tags_div:
            raw_tags = tags_div.get_text(separator=",").replace("tags:", "")
            info["tags"] = [t.strip() for t in raw_tags.split(",") if t.strip()]

        # image
        img = result.find("img")
        if img and img.get("src"):
            info["band_image"] = img["src"]

    driver.quit()
    return info

def enrich_missing_band(band_name, bandcamp_df, csv_path="bandcamp.csv"):
    info = extract_bandcamp_info(band_name)
    new_row = {
        "band": band_name,
        "location": info["location"],
        "bandcamp_url": info["bandcamp_url"],
        "genre": info["genre"],
        "tags": ", ".join(info["tags"]),
        "band_image": info["band_image"],
    }
    bandcamp_df = pd.concat([bandcamp_df, pd.DataFrame([new_row])], ignore_index=True)
    bandcamp_df.to_csv(csv_path, index=False)
    return new_row, bandcamp_df

def enrich(df, bandcamp_lookup, csv_path="bandcamp.csv"):
    if os.path.exists(csv_path):
        bc_df = pd.read_csv(csv_path)
        bandcamp_lookup = bc_df.set_index("band").to_dict(orient="index")
    else:
        bc_df = pd.DataFrame(columns=["band","location","bandcamp_url","genre","tags","band_image"])
        bandcamp_lookup = {}

    def enrich_band_info(band_name):
        nonlocal bc_df, bandcamp_lookup

        if pd.isna(band_name) or not band_name.strip():
            return ""
        bn = band_name.strip()
        info = bandcamp_lookup.get(bn)
        if not info or pd.isna(info.get("bandcamp_url")):
            info, bc_df = enrich_missing_band(bn, bc_df, csv_path)
            bandcamp_lookup[bn] = info

        if not info.get("bandcamp_url"):
            return f"\n{bn}: No Bandcamp found"

        lines = [
            f"{bn}: {info.get('bandcamp_url','')}",
            f"Genre: {info.get('genre','N/A') or 'N/A'}",
            f"Tags: {info.get('tags','N/A') or 'N/A'}",
            f"Location: {info.get('location','N/A') or 'N/A'}",
        ]
        if info.get("band_image"):
            lines.append(f"Image: {info['band_image']}")
        return "\n" + "\n".join(lines)

    df["More Info"] = df["band"].apply(enrich_band_info)
    return df

# ---- RUN IT ALL ----
df = scrape_Tamarack()
df_enriched = enrich(df, bandcamp_lookup=None, csv_path="bandcamp.csv")
print(df_enriched.head())
