import os
import requests
from dotenv import load_dotenv

load_dotenv()

def getPatentes(patente, limit = 10, offset = 0):
    url = "https://connect.patsnap.com/search/patent/query-search-patent/v2"
    headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "limit": limit,
        "offset": offset,
        "collapse_order": "LATEST",
        "collapse_by": "PBD",
        "collapse_type": "DOCDB",
        "query_text": f"TACD: {patente}"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=(5, 30))
    response.raise_for_status()

    try:
        body = response.json()
        
    except ValueError as erro:
        raise ValueError("A API retornou uma resposta inválida.") from erro
    
    # isistance = verifica se o objeto é de uma classe #
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict): 
        raise ValueError("A API retornou dados em um formato inesperado.")
    
    patentes = body["data"].get("results")

    if not isinstance(patentes, list) or any(
        not isinstance(item, dict) for item in patentes
    ):
        raise ValueError("A lista de patentes retornada é invalida.")

    return patentes

def _get(url, params):
    response = requests.get(
        url,
        params=params,
        headers={"Authorization": f"Bearer {os.getenv('API_KEY')}"},
        timeout=(5, 30)
    )

    response.raise_for_status()

    try:
        body = response.json()
    except ValueError as erro:
        raise ValueError("A API retornou uma resposta inválida.") from erro

    if not isinstance(body, dict):
        raise ValueError("A API retornou um formato inesperado.")

    if body.get("status") is not True:
        mensagem = body.get("error_msg", "Não foi possível obter os dados.")
        raise ValueError(mensagem)

    dados = body.get("data")

    if not isinstance(dados, list):
        raise ValueError("A API retornou dados em um formato inesperado.")

    return dados


def getResumo(patent_id, lang="en"):

    #Tenta obter o Abstract original pelo P011
    dados = _get(
        "https://connect.patsnap.com/basic-patent-data/simple-bibliography",
        {"patent_id": patent_id}
    )

    if dados:
        bibliografia = dados[0].get("bibliographic_data", {})
        abstracts = bibliografia.get("abstracts", [])

        for abstract in abstracts:
            texto = abstract.get("text")

            if texto:
                return texto

    #Se não encontrar, tenta o Abstract traduzido pelo P043
    dados = _get(
        "https://connect.patsnap.com/basic-patent-data/abstract-data-translated",
        {
            "patent_id": patent_id,
            "lang": lang,
            "replace_by_related": 1
        }
    )

    if dados:
        return dados[0].get("abstract")

    return None

def getDescricaoOriginal(patent_id, replace_by_related="1"):
    url = "https://connect.patsnap.com/basic-patent-data/description-data"

    headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY')}",
        "Content-Type": "application/json"
    }

    params = {
        "patent_id": patent_id,
        "replace_by_related": replace_by_related
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=(5, 30)
    )

    response.raise_for_status()

    try:
        body = response.json()
    except ValueError as erro:
        raise ValueError("A API retornou uma resposta inválida.") from erro

    print("\nResposta da API P019:")
    print(body)

    if not isinstance(body, dict) or body.get("status") is not True:
        mensagem = body.get("error_msg", "Não foi possível obter a descrição.")
        raise ValueError(mensagem)

    dados = body.get("data")

    if not isinstance(dados, list):
        raise ValueError("A API retornou dados em um formato inesperado.")

    if not dados:
        return None

    return dados[0]

def getReivindicacoes(patent_id, lang="en"):
    
    #tenta as reivindicações originais
    dados = _get(
        "https://connect.patsnap.com/basic-patent-data/claim-data",
        {
            "patent_id": patent_id,
            "replace_by_related": 1
        }
    )

    if dados and dados[0].get("claims"):
        claims = dados[0]["claims"]

        if isinstance(claims, list):
            return claims

        if isinstance(claims, list):
            textos = []

            for claim in claims:
                if claim.get("lang", "").lower() == lang.lower():
                    textos.append(claim.get("claim_text", ""))

            if textos:
                return "\n\n".join(textos) 

    #tenta obter revindicações traduzidas
    dados = _get(
        "https://connect.patsnap.com/basic-patent-data/claim-data-translated",
        {
            "patent_id": patent_id,
            "lang": lang,
            "replace_by_related": 1
        }
    )

    if dados and dados[0].get("claims"):
        return dados[0].get("claims")

    return None
