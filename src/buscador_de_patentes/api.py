import os
import requests
from dotenv import load_dotenv

load_dotenv()

def getPatentes(patente, qtd_patentes):
    url = "https://connect.patsnap.com/search/patent/query-search-patent/v2"
    headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "limit": qtd_patentes,
        "collapse_order": "LATEST",
        "collapse_by": "PBD",
        "collapse_type": "DOCDB",
        "query_text": f"TACD: {patente}"
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    data = response.json()["data"]
    patentes = data.get("results", [])
    
    return patentes
