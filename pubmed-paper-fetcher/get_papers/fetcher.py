import requests
import time
import logging
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET

# Constants
PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
TOOL = "PubMedFetcher"
EMAIL = "saipranavi136@gmail.com"  # Replace with your real email

logger = logging.getLogger(__name__)

def search_pubmed(query: str, retmax: int = 20) -> List[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "retmode": "json",
        "tool": TOOL,
        "email": EMAIL
    }
    response = requests.get(PUBMED_SEARCH_URL, params=params)
    response.raise_for_status()
    return response.json()["esearchresult"]["idlist"]

def fetch_details(pubmed_ids: List[str]) -> List[Dict[str, Optional[str]]]:
    params = {
        "db": "pubmed",
        "id": ",".join(pubmed_ids),
        "retmode": "xml",
        "tool": TOOL,
        "email": EMAIL
    }
    response = requests.get(PUBMED_FETCH_URL, params=params)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    results = []

    for article in root.findall(".//PubmedArticle"):
        try:
            pmid = article.findtext(".//PMID")
            title = article.findtext(".//ArticleTitle")
            pub_date = extract_pub_date(article)
            authors_data = extract_authors(article)

            results.append({
                "PubmedID": pmid,
                "Title": title,
                "Publication Date": pub_date,
                "Non-academic Author(s)": "; ".join(authors_data["non_academic_names"]),
                "Company Affiliation(s)": "; ".join(authors_data["company_affiliations"]),
                "Corresponding Author Email": authors_data["corresponding_email"]
            })
        except Exception as e:
            logger.warning(f"Skipping article due to error: {e}")
            continue

    return results

def extract_pub_date(article: ET.Element) -> str:
    date_elem = article.find(".//PubDate")
    if date_elem is None:
        return "Unknown"
    year = date_elem.findtext("Year") or ""
    month = date_elem.findtext("Month") or ""
    day = date_elem.findtext("Day") or ""
    return f"{year}-{month}-{day}".strip("-")

def extract_authors(article: ET.Element) -> Dict[str, List[str]]:
    non_academic = []
    companies = []
    email = None

    for author in article.findall(".//Author"):
        name = f"{author.findtext('ForeName', '')} {author.findtext('LastName', '')}".strip()
        affiliation_list = author.findall(".//AffiliationInfo/Affiliation")
        for aff in affiliation_list:
            aff_text = aff.text or ""
            aff_lower = aff_text.lower()

            if "university" not in aff_lower and "college" not in aff_lower and "institute" not in aff_lower:
                non_academic.append(name)
                companies.append(aff_text)

            if not email and "@" in aff_text:
                parts = aff_text.split()
                for word in parts:
                    if "@" in word:
                        email = word.strip(".;()")
                        break

    return {
        "non_academic_names": non_academic,
        "company_affiliations": companies,
        "corresponding_email": email or "Not found"
    }
