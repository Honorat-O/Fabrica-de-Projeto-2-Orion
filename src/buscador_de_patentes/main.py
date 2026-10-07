import streamlit as st
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

        if contagem_anos:
            st.subheader("Quantidade de patentes por ano")
            st.line_chart(contagem_anos)
        


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
