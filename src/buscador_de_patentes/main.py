import streamlit as st
import pandas as pd
import plotly.express as px
from api import getPatentes, montarConsulta, montarFiltros, aplicarFiltros
import requests
import math
from datetime import date
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
    /* os ícones do Streamlit são texto (ex: "keyboard_arrow_right") desenhado pela fonte Material Symbols,
       então eles precisam voltar para essa fonte, senão aparecem escritos na tela */
    [data-testid="stIconMaterial"],
    [data-testid="stAlertDynamicIcon"],
    [data-testid="stToastDynamicIcon"],
    [data-testid="stHeadingIcon"],
    [data-testid="stMetricIcon"] {
        font-family: 'Material Symbols Rounded' !important;
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

# autoridades (escritórios de patentes) usadas no filtro AUTHORITY
AUTORIDADES = {
    "US": "Estados Unidos",
    "EP": "Europa (EPO)",
    "WO": "Internacional (WIPO/PCT)",
    "CN": "China",
    "JP": "Japão",
    "KR": "Coreia do Sul",
    "BR": "Brasil",
    "DE": "Alemanha",
    "GB": "Reino Unido",
    "FR": "França",
    "CA": "Canadá",
    "AU": "Austrália",
    "IN": "Índia",
    "RU": "Rússia",
}

# nomes que aparecem nos filtros aplicados, a chave é o field code da PatSnap
NOMES_FILTROS = {
    "PBD": "Publicação",
    "APD": "Aplicação",
    "AUTHORITY": "Autoridade",
    "IPC": "IPC",
    "CPC": "CPC",
    "IN": "Inventor",
    "AN": "Titular",
}

DATA_MINIMA = date(1800, 1, 1)

# troca os filtros aplicados e refaz a pesquisa a partir da primeira página
def trocarFiltros(filtros):
    st.session_state.filtros = filtros
    # mudar a versão recria os campos da barra lateral com os filtros aplicados (ou vazios ao limpar)
    st.session_state.versao_filtros += 1
    st.session_state.pagina_atual = 1
    st.session_state.patentes = None
    st.rerun()

# dois campos de data (De / Até) para os filtros de período
def campoPeriodo(campo, versao):
    inicio, fim = st.session_state.filtros.get(campo, (None, None))
    coluna_inicio, coluna_fim = st.columns(2)

    with coluna_inicio:
        inicio = st.date_input(
            "De",
            value=inicio,
            min_value=DATA_MINIMA,
            max_value=date.today(),
            format="DD/MM/YYYY",
            key=f"{campo}_inicio_{versao}",
        )

    with coluna_fim:
        fim = st.date_input(
            "Até",
            value=fim,
            min_value=DATA_MINIMA,
            max_value=date.today(),
            format="DD/MM/YYYY",
            key=f"{campo}_fim_{versao}",
        )

    return inicio, fim

# barra lateral com os filtros, eles só são aplicados quando o usuário clica em "Aplicar"
def mostrarFiltros():
    filtros = st.session_state.filtros
    versao = st.session_state.versao_filtros

    with st.sidebar:
        st.header("Filtros")

        with st.form("form_filtros", border=False):
            with st.expander("Período", expanded="PBD" in filtros or "APD" in filtros):
                st.caption("Data de publicação")
                pbd_inicio, pbd_fim = campoPeriodo("PBD", versao)

                st.caption("Data de aplicação")
                apd_inicio, apd_fim = campoPeriodo("APD", versao)

            with st.expander("Autoridade", expanded="AUTHORITY" in filtros):
                autoridades = st.multiselect(
                    "Autoridade",
                    list(AUTORIDADES.keys()),
                    default=filtros.get("AUTHORITY", []),
                    format_func=lambda sigla: f"{sigla} - {AUTORIDADES[sigla]}",
                    placeholder="Selecione uma ou mais",
                    label_visibility="collapsed",
                    key=f"AUTHORITY_{versao}",
                )

            with st.expander("Classificação", expanded="IPC" in filtros or "CPC" in filtros):
                ipc = st.text_input("IPC", value=filtros.get("IPC", ""), placeholder="ex: H04L; G06N3/08", key=f"IPC_{versao}")
                cpc = st.text_input("CPC", value=filtros.get("CPC", ""), placeholder="ex: G06N3/08", key=f"CPC_{versao}")

            with st.expander("Inventor e titular", expanded="IN" in filtros or "AN" in filtros):
                inventor = st.text_input("Inventor", value=filtros.get("IN", ""), placeholder="ex: Hinton; LeCun", key=f"IN_{versao}")
                titular = st.text_input("Titular / empresa", value=filtros.get("AN", ""), placeholder="ex: Qualcomm; Samsung", key=f"AN_{versao}")

            st.caption("Para informar mais de um valor, separe com ponto e vírgula (;).")

            coluna_aplicar, coluna_limpar = st.columns(2)

            with coluna_aplicar:
                aplicar = st.form_submit_button("Aplicar", width="stretch")

            with coluna_limpar:
                limpar = st.form_submit_button("Limpar", width="stretch")

    if limpar:
        trocarFiltros({})

    if aplicar:
        # só entram os filtros que foram preenchidos
        novos_filtros = {}

        if pbd_inicio or pbd_fim:
            novos_filtros["PBD"] = (pbd_inicio, pbd_fim)

        if apd_inicio or apd_fim:
            novos_filtros["APD"] = (apd_inicio, apd_fim)

        if autoridades:
            novos_filtros["AUTHORITY"] = autoridades

        for campo, valor in (("IPC", ipc), ("CPC", cpc), ("IN", inventor), ("AN", titular)):
            if valor.strip(" ;"):
                novos_filtros[campo] = valor.strip(" ;")

        try:
            montarFiltros(novos_filtros)
        except ValueError as erro:
            st.sidebar.warning(str(erro))
            return

        if novos_filtros != filtros:
            trocarFiltros(novos_filtros)

# texto curto de cada filtro aplicado, ex: "01/01/2020 a 31/12/2025"
def descreverFiltro(campo, valor):
    if campo in ("APD", "PBD"):
        inicio, fim = valor

        if inicio and fim:
            return f"{inicio:%d/%m/%Y} a {fim:%d/%m/%Y}"

        if inicio:
            return f"a partir de {inicio:%d/%m/%Y}"

        return f"até {fim:%d/%m/%Y}"

    if campo == "AUTHORITY":
        return ", ".join(valor)

    return valor

# mostra os filtros aplicados acima dos resultados, clicar em um deles remove o filtro
def mostrarFiltrosAplicados():
    filtros = st.session_state.filtros

    if not filtros:
        return

    with st.container(horizontal=True, vertical_alignment="center"):
        st.caption("Filtros aplicados:")

        for campo, valor in filtros.items():
            if st.button(
                f"{NOMES_FILTROS[campo]}: {descreverFiltro(campo, valor)}",
                key=f"remover_filtro_{campo}",
                icon=":material/close:",
                help="Remover filtro",
            ):
                novos_filtros = dict(filtros)
                del novos_filtros[campo]
                trocarFiltros(novos_filtros)

def main():
    # Inicializa os estados na memória da sessão
    if "termo" not in st.session_state:
        st.session_state.termo = ""

    if "filtros" not in st.session_state:
        st.session_state.filtros = {}

    if "versao_filtros" not in st.session_state:
        st.session_state.versao_filtros = 0

    if "total_patentes" not in st.session_state:
        st.session_state.total_patentes = 0

    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = 1

    if "patentes" not in st.session_state:
        st.session_state.patentes = None

    if "patente_selecionada" not in st.session_state:
        st.session_state["patente_selecionada"] = None

    # Se o usuário clicou em uma patente, mostra SÓ a área dela:
    if st.session_state["patente_selecionada"] is not None:
        mostrar_detalhes(st.session_state["patente_selecionada"])
        return

    # Caso contrário, mostra a tela normal de busca:
    st.title("🔎 Searchent")
    st.caption("Explore patentes e encontre tecnologias para seus projetos.")

    mostrarFiltros()

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

    mostrarFiltrosAplicados()

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
                # os filtros entram na própria consulta, então resultados, paginação e gráficos usam a mesma pesquisa filtrada
                consulta = aplicarFiltros(termo, st.session_state.filtros)
                patentes, total_patentes = getPatentes(consulta, MAXIMO_PATENTES, 0)

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
        st.session_state.total_patentes = total_patentes

    patentes = st.session_state.patentes

    if not patentes:
        if st.session_state.filtros:
            st.info("Nenhuma patente encontrada com os filtros aplicados.")
        else:
            st.info("Nenhuma patente encontrada para esta pesquisa.")
        return

    # a API devolve o total geral, mas só as primeiras MAXIMO_PATENTES são carregadas
    total_formatado = f"{st.session_state.total_patentes:,}".replace(",", ".")

    if st.session_state.total_patentes > len(patentes):
        st.caption(f"{total_formatado} patentes encontradas (exibindo as {len(patentes)} primeiras).")
    else:
        st.caption(f"{total_formatado} patentes encontradas.")

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