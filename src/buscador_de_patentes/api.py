import os
import requests
from dotenv import load_dotenv

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
        "query_text": patente
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
