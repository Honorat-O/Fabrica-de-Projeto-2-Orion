import os
import requests
from dotenv import load_dotenv
import re

load_dotenv()

# monta o query_text usando os field codes da PatSnap (ex: TTL:(robot), APD:[2020 TO 2025])
def montarConsulta(campo, termo):
    # na pesquisa avançada o usuário já escreve a consulta completa
    if campo == "AVANCADA":
        return termo

    # nos campos de data o usuário informa um ano (2020) ou um período (2020-2025)
    if campo in ("APD", "PBD"):
        anos = termo.replace(" ", "").split("-")
        inicio = anos[0]
        fim = anos[-1]

        if len(anos) > 2 or not all(ano.isdigit() and len(ano) == 4 for ano in (inicio, fim)) or inicio > fim:
            raise ValueError("Informe um ano (ex: 2020) ou um período (ex: 2020-2025).")

        return f"{campo}:[{inicio} TO {fim}]"

    return f"{campo}:({termo})"

# transforma os filtros da barra lateral em expressões do query_text
# filtros = {"PBD": (inicio, fim), "AUTHORITY": ["US", "CN"], "IPC": "H04L; G06N", ...}
def montarFiltros(filtros):
    expressoes = []

    for campo, valor in filtros.items():
        # nas datas o início ou o fim podem ficar em branco, aí a PatSnap usa o "*"
        if campo in ("APD", "PBD"):
            inicio, fim = valor

            if inicio and fim and inicio > fim:
                raise ValueError("A data inicial não pode ser maior que a data final.")

            inicio = inicio.strftime("%Y%m%d") if inicio else "*"
            fim = fim.strftime("%Y%m%d") if fim else "*"
            expressoes.append(f"{campo}:[{inicio} TO {fim}]")

        elif campo == "AUTHORITY":
            expressoes.append(f"AUTHORITY:({' OR '.join(valor)})")

        # nos campos de texto o usuário separa vários valores com ";" (ex: Qualcomm; Samsung)
        else:
            itens = [f"({item.strip()})" for item in valor.split(";") if item.strip()]

            if itens:
                expressoes.append(f"{campo}:({' OR '.join(itens)})")

    return expressoes

# junta a consulta do usuário com os filtros, ex: (TACD:(robot)) AND AUTHORITY:(US OR CN)
def aplicarFiltros(consulta, filtros):
    expressoes = montarFiltros(filtros)

    if not expressoes:
        return consulta

    consulta = " AND ".join([f"({consulta})"] + expressoes)

    if len(consulta) > 3000:
        raise ValueError("A consulta com os filtros passou do limite de 3.000 caracteres.")

    return consulta

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
        "query_text": patente,
        "fields": ["patent_id", "publication_number", "authority", "priority_country"]
    }


    response = requests.post(url, json=payload, headers=headers, timeout=(5, 30))
    response.raise_for_status()

    try:
        body = response.json()

    except ValueError as erro:
        raise ValueError("A API retornou uma resposta inválida.") from erro

    # isistance = verifica se o objeto é de uma classe
    if not isinstance(body, dict):
        raise ValueError("A API retornou dados em um formato inesperado.")

    # a PatSnap responde erros com status 200, então o erro vem no "status" do corpo
    if body.get("status") is False:
        if body.get("error_code") == 68300004:
            raise ValueError("A consulta é inválida. Verifique a sintaxe da pesquisa.")

        raise ValueError(f"O serviço retornou um erro: {body.get('error_msg', 'erro desconhecido')}")

    if not isinstance(body.get("data"), dict):
        raise ValueError("A API retornou dados em um formato inesperado.")

    # quando a pesquisa não encontra nada a API devolve "data": {}
    if not body["data"]:
        return [], 0

    patentes = body["data"].get("results")

    if not isinstance(patentes, list) or any(
        not isinstance(item, dict) for item in patentes
    ):
        raise ValueError("A lista de patentes retornada é invalida.")

    total_patentes = body["data"].get("total_search_result_count")

    if not isinstance(total_patentes, int):
        raise ValueError("A quantidade total de patentes retornada é inválida.")

    return patentes, total_patentes

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