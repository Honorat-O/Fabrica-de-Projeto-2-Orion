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

    response = requests.post(url, json=payload, headers=headers,timeout=(5,30))
    response.raise_for_status()

    try:
        body = response.json()
        
    except ValueError as erro:
        raise ValueError("A API retornou uma resposta inválida.") from erro
    
    # isistance = verifica se o objeto é de uma classe #
    if not isinstance(body,dict) or not isinstance(body.get("data"), dict): 
        raise ValueError("A API retornou dados em um formato inesperado.")

    
    patentes = body["data"].get("results")

    if not isinstance(patentes, list) or any(
        not isinstance(item, dict) for item in patentes
    ):
        raise ValueError("A lista de patentes retornada é invalida.")

    return patentes
