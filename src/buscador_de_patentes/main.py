import streamlit as st
import pandas as pd
import io
import plotly.express as px
from api import getPatentes, montarConsulta, getDescricaoPatente
import requests
import math
from componentes import mostrar_card, mostrar_detalhes, montar_linha_planilha

st.set_page_config(
    page_title="Orion | Buscador de Patentes",
    page_icon="🔎",
    layout="wide",
)
st.markdown(
      """
    <style>
    @import url('https://cdnfonts.com');

    /* 1. Fonte personalizada apenas nos textos e controles */
    html, body, p, h1, h2, h3, h4, h5, h6, label, input, textarea, select, button {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'San Francisco', sans-serif !important;
    }

    /* 2. Preserva os ícones nativos do Streamlit */
    [data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded' !important;
    }

    /* 3. Trava a largura da sidebar APENAS quando estiver aberta */
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 280px !important;
        max-width: 280px !important;
        width: 280px !important;
        border-right: 1px solid #1F2937;
    }

    /* 4. Permite que a sidebar recolha 100% quando estiver fechada */
    [data-testid="stSidebar"][aria-expanded="false"] {
        min-width: 0px !important;
        max-width: 0px !important;
        width: 0px !important;
    }

    /* 5. Desativa a alça de redimensionamento na borda sem quebrar o layout */
    [data-testid="stSidebar"] > div:nth-child(2) {
        pointer-events: none !important;
        cursor: default !important;
    }

    /* 6. Ajusta o botão 'X' dentro do expander para não cortar o símbolo */
    [data-testid="stSidebar"] [data-testid="stExpander"] button {
        padding: 0px 8px !important;
        min-height: 28px !important;
        height: 28px !important;
    }

    /* 7. Estilo mais sóbrio para o botão principal (Gerar Planilha Excel) */
    [data-testid="stSidebar"] button[kind="primary"] {
        background-color: #2563EB !important;
        border: 1px solid #3B82F6 !important;
        color: #FFFFFF !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out;
    }

    [data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
        border-color: #60A5FA !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

MAXIMO_PATENTES = 1000
ITENS_POR_PAGINA = 10

TIPOS_PESQUISA = {
    "Palavras-chave": "TACD",
    "Título": "TTL",
    "Resumo": "ABST",
    "Reivindicações": "CLMS",
    "Descrição": "DESC",
    "Número da patente (ex: US11205304B2)": "PN",
    "Número do pedido (ex: US17/521392)": "APNO",
    "Ano de aplicação (ex: 2020 ou 2020-2025)": "APD",
    "Ano de publicação (ex: 2020 ou 2020-2025)": "PBD",
    "Classificação IPC (ex: H04L ou B60Q1/00)": "IPC",
    "Classificação CPC (ex: A46B11/0055)": "CPC",
    "Inventor": "IN",
    "Titular / empresa": "AN",
    "Pesquisa avançada (ex: TTL:robot AND APD:[2020 TO 2025])": "AVANCADA",
}

def main():
    # Inicializa os estados na memória da sessão
    if "termo" not in st.session_state:
        st.session_state.termo = ""

    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = 1

    if "patentes" not in st.session_state:
        st.session_state.patentes = None

    if "patente_selecionada" not in st.session_state:
        st.session_state.patente_selecionada = None

    if "patentes_salvas" not in st.session_state:
        st.session_state.patentes_salvas = {}

    # Se o usuário clicou em uma patente, mostra SÓ a área dela:
    if st.session_state["patente_selecionada"] is not None:
        mostrar_detalhes(st.session_state["patente_selecionada"])
        return

    # Barra lateral com o contador e botão de exportação sempre a mostra na tela normal
    with st.sidebar:
        st.header("Lista de Exportação")
        qtd_salvas = len(st.session_state.patentes_salvas)
        st.write(f"Patentes selecionadas: **{qtd_salvas}**")

        if qtd_salvas > 0:
            # 1. Lista individual com botão para remover cada patente
            with st.expander("Ver / remover itens", expanded=True):
                for pn_salvo in list(st.session_state.patentes_salvas.keys()):
                    col_pn, col_rem = st.columns([4, 1], vertical_alignment="center")
                    with col_pn:
                        st.markdown(
                            f"<span style='font-size: 13px; white-space: nowrap;'>• {pn_salvo}</span>",
                            unsafe_allow_html=True
                        )
                    with col_rem:
                        if st.button("✕", key=f"rem_{pn_salvo}", help=f"Remover {pn_salvo}"):
                            del st.session_state.patentes_salvas[pn_salvo]
                            st.rerun()

            # 2. Botão para limpar toda a lista de uma vez
            if st.button("Limpar tudo", use_container_width=True):
                st.session_state.patentes_salvas = {}
                st.rerun()

            st.divider()

            # 3. Geração e download da planilha Excel
            if st.button("Gerar Planilha Excel", type="primary", use_container_width=True):
                linhas = []
                with st.spinner("Buscando descrições e montando planilha..."):
                    for pn, pat in st.session_state.patentes_salvas.items():
                        descricao = getDescricaoPatente(
                            patent_id=pat.get("patent_id"),
                            pn=pn
                        )
                        linhas.append(montar_linha_planilha(pat, descricao))

                df_planilha = pd.DataFrame(linhas)
                buffer = io.BytesIO()
                df_planilha.to_excel(buffer, index=False, engine="openpyxl")

                st.download_button(
                    label="Baixar arquivo .xlsx",
                    data=buffer.getvalue(),
                    file_name="patentes_selecionadas.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    # Caso contrário, mostra a tela normal de busca:
    st.title("Searchent")
    st.caption("Explore patentes e encontre tecnologias para seus projetos.")

    with st.form("form_busca_patente", border=False):
        tipo_pesquisa = st.selectbox("Tipo de pesquisa", list(TIPOS_PESQUISA.keys()), label_visibility="collapsed")

        coluna_busca, coluna_botao = st.columns([5, 1])

        with coluna_busca:
            patente = st.text_input(
                "Termo de busca",
                type="search",
                placeholder="Insira o termo da pesquisa",
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
            termo = montarConsulta(TIPOS_PESQUISA[tipo_pesquisa], termo)
        except ValueError as erro:
            st.warning(str(erro))
            return

        st.session_state.termo = termo
        st.session_state.pagina_atual = 1
        st.session_state.patentes = None

    termo = st.session_state.termo

    if not termo:
        return

    if st.session_state.patentes is None:
        try:
            #aqui, enquanto a pesquisa carrega, aparece essa mensagem e a bolinha rodando
            with st.spinner("Buscando patentes..."):
                patentes, total_patentes = getPatentes(termo, MAXIMO_PATENTES, 0)

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

        st.session_state.patentes = patentes

    patentes = st.session_state.patentes

    if not patentes:
        st.info("Nenhuma patente encontrada para esta pesquisa.")
        return

    paginas =math.ceil(len(patentes) / ITENS_POR_PAGINA)
    offset = (st.session_state.pagina_atual - 1) * ITENS_POR_PAGINA
    patentes_pagina = patentes[offset:offset + ITENS_POR_PAGINA]

    #fiz aqui um expander para colocar os gráficos e ficar mais organizado

    with st.expander("Detalhes e gráficos", expanded=False):
        st.subheader("Patentes")

        #essa contagem eu fiz para usar no grafico, ele foi feito com base nas datas de publicação
        contagem_anos = {}
        for p in patentes:
            data = str(p.get("pbdt", ""))
            if data and len(data) >=4:
                ano = data[0:4]

                if ano in contagem_anos:
                    contagem_anos[ano] +=1
                else:
                    contagem_anos[ano] = 1

        #aqui, após fazer a contagem de quantas pesquisas tem em cada ano, eu coloco os dados no grafico (st.line_chart)
        #dei uma leve alterada pra quando passar o mouse por cima do gráfico aparecer "Ano" e "Quantidade", isso foi mais chato do que eu achei que seria
        if contagem_anos:
            st.subheader("Quantidade de patentes por ano")

            df_anos = pd.DataFrame({
            "Quantidade": contagem_anos
            }).rename_axis("Ano").reset_index()

            st.line_chart(
                df_anos,
                x="Ano",
                y="Quantidade"
            )

        #agora aqui eu fiz um gráfico de empresas com mais patentes
        #primeiro eu fiz uma contagem de quanto cada empresa tem de patentes do tema

        contagem_empresas = {}
        for p in patentes:
            empresa = p.get("current_assignee", "Não informado")

            if empresa and empresa != "Não informado":
                contagem_empresas[empresa] = (
                    contagem_empresas.get(empresa, 0) + 1
                )

        #agora faço o grafico com o st.bar_chart
        #quando tirarmos a limitação de pesquisa, da pra fazer algo como só aparecer as 20 que mais tem ou algo do tipo

        if contagem_empresas:
            df_empresas = pd.DataFrame(
                list(contagem_empresas.items()),
                columns = ["Depositante", "Quantidade"]
            )
            df_empresas = df_empresas.sort_values(
                "Quantidade", ascending=False
            )

            st.subheader("Principais titulares de patentes")
            st.bar_chart(
            df_empresas,
            x="Depositante",
            y="Quantidade"
            )


        # --- COLOQUE ESTE TRECHO DENTRO DO SEU EXPANDER ---

        st.subheader("Distribuição Global de Patentes")

        # Dicionário de conversão de Sigla ISO-2 para Nome em Inglês (aceito pelo Plotly)
        mapa_paises = {
            "BR": "Brazil", "US": "United States", "CN": "China", "JP": "Japan",
            "KR": "South Korea", "DE": "Germany", "FR": "France", "GB": "United Kingdom",
            "CA": "Canada", "AU": "Australia", "IN": "India", "RU": "Russia",
            "IT": "Italy", "ES": "Spain", "CH": "Switzerland", "NL": "Netherlands",
            "SE": "Sweden", "FI": "Finland", "NO": "Norway", "DK": "Denmark"
        }

        contagem_paises = {}
        for p in patentes:
            sigla = p.get("authority", "Não informado")
            if sigla and sigla != "Não informado":
                # Traduz a sigla para o nome do país. Se não estiver no dicionário, mantém a sigla
                nome_pais = mapa_paises.get(sigla, sigla)
                contagem_paises[nome_pais] = contagem_paises.get(nome_pais, 0) + 1

        if contagem_paises:
            # Criamos o DataFrame com os nomes convertidos
            df_paises = pd.DataFrame(
                list(contagem_paises.items()),
                columns=["País", "Quantidade"]
            )

            # Criando o mapa corrigido
            fig = px.choropleth(
                df_paises,
                locations="País",
                locationmode="country names",  # Mudamos para 'country names' que é aceito pelo Plotly
                color="Quantidade",
                hover_name="País",
                color_continuous_scale=px.colors.sequential.Plasma,
                title="Volume de Patentes por País de Origem (Authority)"
            )

            fig.update_layout(
                margin={"r":0,"t":40,"l":0,"b":0},
                geo=dict(showframe=False, showcoastlines=True)
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Dados de geolocalização não disponíveis para estas patentes.")

    # Exibe os cards salvos na sessão
    for i, resultado in enumerate(patentes_pagina):
        mostrar_card(resultado, i)

    if paginas > 0:
        pagina_atual = st.pagination(paginas, key="pagina_atual")

if __name__ == "__main__":
    main()