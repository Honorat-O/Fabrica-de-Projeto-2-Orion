import streamlit as st
from api import getPatentes
import requests
from componentes import mostrar_card, mostrar_detalhes

st.set_page_config(
    page_title="Orion | Buscador de Patentes",
    page_icon="🔎",
    layout="wide",
)
st.markdown(
    """
    <style>
    @import url('https://fonts.cdnfonts.com/css/sf-pro-display');
    html, body, [class*="css"], [data-testid="stAppViewContainer"] * {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'San Francisco', sans-serif !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
itens = 10;
itens_por_pagina = 10;
maximo_paginas_visiveis = 5;
paginas = itens // itens_por_pagina;

def main():
    # Inicializa os estados na memória da sessão
    if "patentes" not in st.session_state:
        st.session_state["patentes"] = []
    if "patente_selecionada" not in st.session_state:
        st.session_state["patente_selecionada"] = None

    # Se o usuário clicou em uma patente, mostra SÓ a área dela:
    if st.session_state["patente_selecionada"] is not None:
        mostrar_detalhes(st.session_state["patente_selecionada"])
        return

    # Caso contrário, mostra a tela normal de busca:
    st.title("🔎 Searchent")
    st.caption("Explore patentes e encontre tecnologias para seus projetos.")

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

    if enviado:
        termo = patente.strip()
        if not termo:
            st.warning("Digite um termo para pesquisar.")
            return

        try:
            with st.spinner("Buscando patentes..."):
                st.session_state["patentes"] = getPatentes(termo, itens)

        except requests.exceptions.Timeout:
            st.error("A busca demorou demais. Tente novamente.")
            return

        except requests.exceptions.ConnectionError:
            st.error(
                "Não foi possível conectar ao serviço de patentes. "
                "Verifique sua conexão e tente novamente."
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

    # Exibe os cards salvos na sessão
    for i, resultado in enumerate(st.session_state["patentes"][:itens_por_pagina]):
        mostrar_card(resultado, i)
        
if __name__ == "__main__":
    main()