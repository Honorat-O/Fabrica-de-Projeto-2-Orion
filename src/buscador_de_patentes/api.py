import os
import requests
from dotenv import load_dotenv

load_dotenv()


def _get_api_headers(content_type=False):
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente API_KEY não foi configurada.")

    headers = {"Authorization": f"Bearer {api_key}"}
    if content_type:
        headers["Content-Type"] = "application/json"
    return headers


def getPatentes(patente, limit=10, offset=0, filtros=None):
    url = "https://connect.patsnap.com/search/patent/query-search-patent/v2"
    headers = _get_api_headers(content_type=True)

    filtros = filtros or {}
    partes_query = [f"TACD: {patente}"]

    if filtros.get("agencia"):
        partes_query.append(f"AGENCY: {filtros['agencia']}")
    if filtros.get("inventor"):
        partes_query.append(f"INVENTOR: {filtros['inventor']}")
    if filtros.get("data__inicio") and filtros.get("data__fim"):
        partes_query.append(
            f"PBDT:[{filtros['data__inicio']} TO {filtros['data__fim']}]"
        )
    if filtros.get("status_legal"):
        partes_query.append(f"SIMPLE_LEGAL_STATUS: {filtros['status_legal']}")
    if filtros.get("ipc"):
        partes_query.append(f'IPC: {filtros["ipc"]}')

    query_final = " AND ".join(partes_query)

    payload = {
        "limit": limit,
        "offset": offset,
        "collapse_order": "LATEST",
        "collapse_by": "PBD",
        "collapse_type": "DOCDB",
        "query_text": query_final,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=(5, 30))
    response.raise_for_status()

    try:
        body = response.json()
    except ValueError as erro:
        raise ValueError("A API retornou uma resposta inválida.") from erro

    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        raise ValueError("A API retornou dados em um formato inesperado.")

    patentes = body["data"].get("results")

    if not isinstance(patentes, list) or any(
        not isinstance(item, dict) for item in patentes
    ):
        raise ValueError("A lista de patentes retornada é invalida.")

    return patentes


def getDetalhesPatente(patente_id):
    """Retorna bibliografia: abstract, inventores, agência e classificações."""
    url = "https://connect.patsnap.com/basic-patent-data/bibliography"
    headers = _get_api_headers()
    params = {"patent_id": patente_id}
    response = requests.get(url, headers=headers, params=params, timeout=(5, 30))
    response.raise_for_status()

    try:
        body = response.json()
    except ValueError as erro:
        raise ValueError("A API retornou uma resposta inválida.") from erro

    if not isinstance(body, dict):
        raise ValueError("A API retornou dados em um formato inesperado.")

    dados = body.get("data")
    if not isinstance(dados, list) or not dados:
        raise ValueError("Nenhum detalhe encontrado para a patente especificada.")

    return dados[0]


def getClassificacaoPatente(patente_id):
    """Retorna a descrição e as claims da patente."""
    url = "https://connect.patsnap.com/basic-patent-data/classification"
    headers = _get_api_headers()
    params = {"patent_id": patente_id}
    response = requests.get(url, headers=headers, params=params, timeout=(5, 30))
    response.raise_for_status()

    try:
        body = response.json()
    except ValueError as erro:
        raise ValueError("A API retornou uma resposta inválida.") from erro

    if not isinstance(body, dict):
        raise ValueError("A API retornou dados em um formato inesperado.")

    dados = body.get("data")
    if not isinstance(dados, list) or not dados:
        raise ValueError("Nenhuma classificação encontrada para a patente especificada.")

    return dados[0]