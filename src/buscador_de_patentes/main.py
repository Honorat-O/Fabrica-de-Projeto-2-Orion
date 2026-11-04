import streamlit as st
from api import getPatentes
import requests
import math

TOTAL_ITENS = 1000
ITENS_POR_PAGINA = 10

def main():
    if "termo" not in st.session_state:
        st.session_state.termo = ""

    # Container de Busca
    with st.container(horizontal=True, horizontal_alignment="center"):
        st.title("Busque sua patente aqui:")
        with st.form("form_busca_patente", border=False):
            patente = st.text_input("Patente", type="search", placeholder="Insira uma patente aqui", label_visibility="collapsed")
            enviado = st.form_submit_button("Buscar")      
    
    if enviado:
        termo = patente.strip()

        if not termo:
            st.warning("Digite um termo para pesquisar.")
            return

        st.session_state.termo = termo

    termo = st.session_state.termo

    if not termo:
        return

    paginas = math.ceil(TOTAL_ITENS / ITENS_POR_PAGINA)
    pagina_atual = st.pagination(paginas)
    offset = (pagina_atual - 1) * ITENS_POR_PAGINA

    try:
        with st.spinner("Buscando patentes..."):
            patentes = getPatentes(termo, ITENS_POR_PAGINA, offset)

    except requests.exceptions.Timeout:
        st.error("A busca demorou demais. Tente novamente.")
        return

    except requests.exceptions.ConnectionError:
        st.error("Não foi possível conectar ao serviço de patentes. "
                 "Verifiquei sua conexão e tente novamente."
        )
        return

    except requests.exceptions.HTTPError as erro:
        status = (
            erro.response.status_code
            if erro.response is not None
            else None
        )

        if status == 401:
            st.error("A autenticação falhou. Verifique a chave da API.")
        elif status == 403:
            st.error("O serviço recusou o acesso. Verifique as permissões.")
        elif status == 429:
            st.error(
                "O limite de consultas foi atingido. "
                "Aguarde um pouco antes de tentar novamente."
            )
        else:
            st.error("O serviço não conseguiu concluir a busca.")

        return

    except requests.exceptions.RequestException:
        st.error("Ocorreu uma falha na comunicação com o serviço.")
        return

    except ValueError as erro:
        st.error(str(erro))
        return

    for resultado in patentes:
        with st.container(horizontal_alignment="center", border=True):
            st.write(resultado.get("title", "Título não informado."))
            st.write(resultado.get("pn", "PN não informado."))
            st.write(resultado.get("current_assignee", "Não informado."))

if __name__ == "__main__":
    main()