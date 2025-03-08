import requests
from bs4 import BeautifulSoup
import spacy
import csv

# Load spaCy NER model
nlp = spacy.load("en_core_web_sm")

# Headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
}

# URL to fetch company tickers and CIKs
url = "https://www.sec.gov/files/company_tickers.json"

# URL to fetch 8-K filings for a given CIK

def get_filings(cik, count=10):
    search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik:010d}&type=8-K&count={count}&output=atom"
    response = requests.get(search_url, headers=headers, timeout=10)
    return response.text if response.ok else None

# Function to parse the XML response and extract filing information
def parse_filings(filings_xml):
    soup = BeautifulSoup(filings_xml, "xml")
    entry = soup.find("entry")  # Get only the latest filing
    if entry:
        title = entry.title.get_text() if entry.title else "N/A"
        summary = entry.summary.get_text() if entry.summary else "No description"
        filing_time = entry.updated.get_text() if entry.updated else "N/A"
        return {"title": title, "summary": summary[:180], "filing_time": filing_time}
    return None

# Function to extract product info using spaCy NER
def extract_product_info(description):
    doc = nlp(description)
    product_info = {"Company Name": "N/A", "New Product": "N/A"}
    for ent in doc.ents:
        if ent.label_ == "ORG": product_info["Company Name"] = ent.text
        if ent.label_ == "PRODUCT": product_info["New Product"] = ent.text
    return product_info

# Main function
def main():
    # Fetch CIK data
    cik_data = requests.get(url, headers=headers).json()

    # Process first 100 companies
    structured_data = []
    for company in list(cik_data.values())[:100]:
        cik = int(company['cik_str'])
        ticker = company['ticker']
        filings_xml = get_filings(cik)
        if filings_xml:
            filing = parse_filings(filings_xml)
            if filing:
                product_info = extract_product_info(filing["summary"])
                structured_data.append([
                    company['title'], ticker, filing["filing_time"],
                    product_info["New Product"], filing["summary"]
                ])

    # Save data to CSV if available
    if structured_data:
        with open("8k_filings.csv", "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter='|')
            writer.writerow(["Company Name", "Stock Name", "Filing Time", "New Product", "Product Description"])
            writer.writerows(structured_data)
        print("Data saved to 8k_filings.csv")
    else:
        print("No data to save to CSV.")

if __name__ == "__main__":
    main()
