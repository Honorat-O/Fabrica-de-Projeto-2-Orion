import streamlit as st
import pandas as pd
from api import getPatentes, getResumo, getDescricaoOriginal, getReivindicacoes
import requests
import math
from bs4 import BeautifulSoup

TOTAL_ITENS = 1000
ITENS_POR_PAGINA = 10

def formatar_descricao(texto):
    soup = BeautifulSoup(texto, "html.parser")

    for elemento in soup.select("b.d_n"):
        numero = elemento.get_text(strip=True)
        elemento.replace_with(f"\n\n{numero} ")

    return soup.get_text(separator=" ", strip=True)

def formatar_reivindicacoes(texto):
    resultado = []

    # Se receber uma lista de reivindicações
    if isinstance(texto, list):
        for claim in texto:
            if isinstance(claim, dict):
                conteudo = claim.get("claim_text", "")
                numero = claim.get("num", "")
                idioma = claim.get("lang", "")

            if conteudo:
                soup = BeautifulSoup(conteudo, "html.parser")
                conteudo = soup.get_text(" ", strip=True)

                # Separa as reivindicações numeradas
                import re
                conteudo = re.sub(
                    r"(?<!^)(?<!\n)\s+(\d+)\.\s+",
                    r"\n\n\1. ",
                    conteudo
                )

                resultado.append((
                    f"Reivindicação {numero} ({idioma})",
                    conteudo
                ))

        return resultado

    # Se receber uma string HTML
    if isinstance(texto, str):
        soup = BeautifulSoup(texto, "html.parser")

        agrupadas = {}

        for elemento in soup.select(".indep-clm, .dep-clm"):
            numero = elemento.get("num", "")

            if not numero:
                continue

            classes = elemento.get("class", [])
            tipo = "Independente" if "indep-clm" in classes else "Dependente"
            pai = elemento.get("parent", "")
            conteudo = elemento.get_text(" ", strip=True)

            if not conteudo:
                continue

            if numero not in agrupadas:
                agrupadas[numero] = {
                    "tipo": tipo,
                    "pai": pai,
                    "partes": []
                }

            agrupadas[numero]["partes"].append(conteudo)

        for numero, dados in agrupadas.items():
            if dados["tipo"] == "Independente":
                titulo = f"Reivindicação {numero} - Independente"
            else:
                titulo = f"Reivindicação {numero} - Dependente (refere-se à {dados['pai']})"

            conteudo = " ".join(dados["partes"])
            resultado.append((titulo, conteudo))

    return resultado

def main():
    if "termo" not in st.session_state:
        st.session_state.termo = ""

    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = 1

    if "patente_selecionada" not in st.session_state:
        st.session_state.patente_selecionada = None

    if "detalhes_extras" not in st.session_state:
        st.session_state.detalhes_extras = {}

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
        st.session_state.pagina_atual = 1

    termo = st.session_state.termo

    if not termo:
        return

    paginas = math.ceil(TOTAL_ITENS / ITENS_POR_PAGINA)
    offset = (st.session_state.pagina_atual - 1) * ITENS_POR_PAGINA

    try:
        #aqui, enquanto a pesquisa carrega, aparece essa mensagem e a bolinha rodando
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

            import plotly.express as px

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

    # Container de cards de patente
    with st.container():
        for patente in patentes[:ITENS_POR_PAGINA]:
            patent_id = patente.get("patent_id")

            with st.container(horizontal_alignment="center", border=True):
                titulo_patente = (f"{patente.get("title", "Título não informado")}")
                
                #aqui com o st.markdown, da pra modificiar o texto com html, então deixei ele no formato de titulo
                st.markdown(
                    f"<h2 style = 'font-size: 28px; font-weight: bold; '>{titulo_patente}</h2>",
                    unsafe_allow_html=True
                )
                
                st.write(f"SN: {patente.get("pn", "PN não informado")}")
                st.write(f"Autors: {patente.get("current_assignee", "Não informado")}")
                
                #aqui, como a data tava como YYYYMMDD, eu transformei ela em string e formatei ela pra colocar no padrão brasileiro e apresentar no front
                def formatar_data(data):
                    if not data:
                        return "Data não informada"
                    data = str(data)

                    if len(data) != 8 or not data.isdigit():
                        return "Data inválida"

                    return f"{data[6:8]}/{data[4:6]}/{data[0:4]}"
                
                data_publicacao = formatar_data(patente.get("pbdt"))
                st.write(f"Date: {data_publicacao}")
                #aqui eu apresentei o país que foi feita a patente
                st.write(f"Authority: {patente.get("authority", "Não informado")}")

                if st.button("Ver detalhes", key=f"detalhes_{patent_id}"):
                    st.session_state.patente_selecionada = patent_id

                if st.session_state.patente_selecionada == patent_id:
                    st.divider()
                    st.subheader("Detalhes da patente")

                    #info bibliograficas
                    st.write("**Título:**", titulo_patente)
                    st.write("**Número de publicação:**", patente.get("pn", "Não informado"))
                    st.write("**Número do pedido:**", patente.get("apno", "Não informado"))
                    st.write("**Titular original:**", patente.get("original_assginee", "Não informado"))
                    st.write("**Titular Atual:**", patente.get("current_assignee", "Não informado"))
                    st.write("**Inventor(es):**", patente.get("inventor", "Não informado"))
                    st.write("**Data de depósito:**", formatar_data(patente.get("apdt")))
                    st.write("**Data da publicação:**", data_publicacao)
                    st.write("**Jurisdição:**", patente.get("authority", "Não informado"))

                    #verifica se os detalhes ja foram consultados
                    if patent_id not in st.session_state.detalhes_extras:
                        extras = {
                            "resumo": None,
                            "descricao": None,
                            "reivindicacoes": None,
                            "erro_resumo": None,
                            "erro_descricao": None,
                            "erro_reivindicacoes": None
                        }

                        with st.spinner("Buscando informações adicionais..."):

                            #consulta o abstract
                            try:
                                extras["resumo"] = getResumo(patent_id)
                            except (requests.exceptions.RequestException, ValueError) as erro:
                                extras["erro_resumo"] = str(erro)

                            #consulta a descricao completa
                            try:
                                extras["descricao"] = getDescricaoOriginal(patent_id)
                            except (requests.exceptions.RequestException, ValueError) as erro:
                                extras["erro_descricao"] = str(erro)

                            #consulta as reivindicações
                            try:
                                extras["reivindicacoes"] = getReivindicacoes(patent_id)
                            except (requests.exceptions.RequestException, ValueError) as erro:
                                extras["erro_reivindicacoes"] = str(erro)

                        st.session_state.detalhes_extras[patent_id] = extras

                    extras = st.session_state.detalhes_extras[patent_id]

                    st.divider()

                    #apresenta o abstract
                    st.subheader("Resumo da invenção")

                    if extras["erro_resumo"]:
                        st.warning(f"Não foi possível obter o resumo: {extras['erro_resumo']}")

                    elif extras["resumo"]:
                        st.write(extras["resumo"])

                    else:
                        st.info("Resumo não disponível para esta patente")

                    #apresenta a descrição completa
                    with st.expander("Descrição completa da invenção", expanded=False):

                        if extras["erro_descricao"]:
                            st.warning(f"Não foi possível obter a descrição: {extras['erro_descricao']}")

                        elif extras["descricao"] is None:
                            st.info("Descrição não disponível para esta patente.")

                        else:
                            descricao = extras["descricao"].get("description", [])

                            if isinstance(descricao, list) and descricao:

                                for parte in descricao:
                                    idioma = parte.get("lang", "Não informado")
                                    texto = parte.get("text", "")

                                    if texto:
                                        texto = formatar_descricao(texto)

                                        st.caption(f"idioma original: {idioma}")
                                        st.write(texto)

                            elif isinstance(descricao, str) and descricao:
                                st.write(descricao)

                            else:
                                st.info("Não foi encontrado texto de descrição.")


                    #apresenta as reivindicações
                    st.subheader("Reivindicações da patente")

                    if extras["erro_reivindicacoes"]:
                        st.warning(
                            f"Não foi possível obter as reivindicações: "
                            f"{extras['erro_reivindicacoes']}"
                        )

                    elif extras["reivindicacoes"]:
                        reivindicacoes = formatar_reivindicacoes(
                            extras["reivindicacoes"]
                        )

                        if reivindicacoes:
                            for titulo, conteudo in reivindicacoes:
                                with st.expander(titulo):
                                    st.write(conteudo)

                        else:
                            st.info("Não doram encontradas reivindicações.")

                    else:
                        st.info("Reivindicações não disponíveis para esta patente.")

                    #botão para fechar os detalhes
                    if st.button("Fechar detalhes", key=f"fechar_{patent_id}"):
                        st.session_state.patente_selecionada = None
                        st.rerun()

    pagina_atual = st.pagination(paginas, key="pagina_atual")

if __name__ == "__main__":
    main()