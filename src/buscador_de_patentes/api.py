import os
import requests
from dotenv import load_dotenv
import re

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
        "query_text": f"TACD: {patente}",
        "fields": ["patent_id", "publication_number", "authority", "priority_country"]
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

def getImagemPatente(patent_id=None, pn=None):
    url = "https://connect.patsnap.com/basic-patent-data/abstract-image"
    headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY')}",
        "Content-Type": "application/json"
    }
    params = {}
    if patent_id:
        params["patent_id"] = patent_id
    elif pn:
        params["patent_number"] = pn
    try:
        response = requests.get(url, headers=headers, params=params, timeout=(5, 30))
        if not response.ok:
            return None

        body = response.json()
    except (requests.exceptions.RequestException, ValueError):
        return None
    dados = body.get("data")

    if isinstance(dados, list) and len(dados) > 0:
        desenho = dados[0].get("abstract_drawing")
        if isinstance(desenho, dict):
            return desenho.get("path")

    return None

def getDescricaoPatente(patent_id=None, pn=None):
    url = "https://connect.patsnap.com/basic-patent-data/simple-bibliography"
    headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY')}",
        "Content-Type": "application/json"
    }
    params = {}
    if patent_id:
        params["patent_id"] = patent_id
    elif pn:
        params["patent_number"] = pn

    try:
        response = requests.get(url, headers=headers, params=params, timeout=(5, 30))
        if not response.ok:
            return None
        body = response.json()
    except (requests.exceptions.RequestException, ValueError):
        return None

    dados = body.get("data")
    if isinstance(dados, list) and len(dados) > 0:
        biblio = dados[0].get("bibliographic_data") or {}
        resumos = biblio.get("abstracts") or []
        if isinstance(resumos, list) and len(resumos) > 0:
            texto = resumos[0].get("text")
            if texto:
                # Remove tags XML/HTML que às vezes vêm junto do texto da patente
                return re.sub(r"<[^>]+>", "", texto).strip()

    return None