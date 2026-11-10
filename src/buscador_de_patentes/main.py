import streamlit as st
import pandas as pd
from api import getPatentes

itens = 30;
itens_por_pagina = 30;
maximo_paginas_visiveis = 5;
paginas = itens // itens_por_pagina;

def main():
    # Container de Busca
    with st.container(horizontal=True, horizontal_alignment="center"):
        st.title("Busque sua patente aqui:")
        with st.form("form_busca_patente", border=False):
            patente = st.text_input("Patente", type="search", placeholder="Insira uma patente aqui", label_visibility="collapsed")
            enviado = st.form_submit_button("Buscar")      
    
    if enviado and patente:
        #aqui, enquanto a pesquisa carrega, aparece essa mensagem e a bolinha rodando
        with st.spinner("Please, wait..."):
        # Parametros do getPatentes(texto do input, quantidade total de patentes para serem buscadas)
            patentes = getPatentes(patente, itens)

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


        if not patentes:
            st.write("Nenhuma patente foi encontrada.")
        else:
            # Container de cards de patente
            with st.container():
                for patente in patentes[:itens_por_pagina]:
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
                            return f"{data[6:8]}/{data[4:6]}/{data[0:4]}"
                        data_publicacao = formatar_data(patente.get("pbdt"))
                        st.write(f"Date: {data_publicacao}")
                        #aqui eu apresentei o país que foi feita a patente
                        st.write(f"Authority: {patente.get("authority", "Não informado")}")

    elif enviado and not patente:
        st.write("Você precisa inserir alguma coisa na caixa de texto para buscar patentes")

if __name__ == "__main__": 
    main()
