import streamlit as st
from api import getPatentes
import requests
from componentes import mostrar_card

st.set_page_config(
    page_title="Orion | Buscador de Patentes",
    page_icon="🔎",
    layout="wide",
)

itens = 10;
itens_por_pagina = 10;
maximo_paginas_visiveis = 5;
paginas = itens // itens_por_pagina;

def main():
    st.title("🔎 Searchent")
    st.caption(
        "Explore patentes e encontre tecnologias para seus projetos."
    )

    with st.form("form_busca_patente", border=False):
        coluna_busca, coluna_botao = st.columns([5, 1])

        with coluna_busca:
            patente = st.text_input(
                "Termo de busca",
                placeholder="Digite apenas termos em inglês.EX: tractor, car, plant...",
                label_visibility="collapsed",
            )

        with coluna_botao:
            enviado = st.form_submit_button(
                "Buscar",
                use_container_width=True,
            )

    st.divider()    
    
    if not enviado:
        return
    
    termo = patente.strip()

    if not termo:
        st.warning("Digite um termo para pesquisar.")
        return

    try:
        with st.spinner("Buscando patentes..."):
            patentes = getPatentes(termo,itens)

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

    for resultado in patentes[:itens_por_pagina]:
        mostrar_card(resultado)
        
if __name__ == "__main__":
    main()