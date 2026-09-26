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

    data = response.json()
    patentes = []

    for i in range(qtd_patentes):
        patente = data["data"]["results"][i]
        patentes.append(patente)

    return patentes
