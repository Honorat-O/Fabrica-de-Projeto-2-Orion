import os
import requests
from dotenv import load_dotenv

load_dotenv()

def getPatente(patente):
    url = "https://connect.patsnap.com/search/patent/query-search-patent/v2"
    headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "limit": 1,
        "collapse_order": "LATEST",
        "collapse_by": "PBD",
        "collapse_type": "DOCDB",
        "query_text": f"TACD: {patente}"
    }

    response = requests.post(url, json=payload, headers=headers)

    data = response.json()

    primeira_patente = data["data"]["results"][0]

    numero_patente = primeira_patente["pn"]
    titulo = primeira_patente["title"]
    empresa = primeira_patente["current_assignee"]

    return numero_patente, titulo, empresa
