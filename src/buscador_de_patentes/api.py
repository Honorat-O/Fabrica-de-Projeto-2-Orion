import os
import requests
from dotenv import load_dotenv

load_dotenv()

# API
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
    "query_text": "TACD: virtual reality"
}

response = requests.post(url, json=payload, headers=headers)

data = response.json()

primeira_patente = data["data"]["results"][0]

numero_patente = primeira_patente["pn"]
titulo = primeira_patente["title"]
empresa = primeira_patente["current_assignee"]

print(f"Número da Patente: {numero_patente}")
print(f"Título: {titulo}")
print(f"Empresa: {empresa}")