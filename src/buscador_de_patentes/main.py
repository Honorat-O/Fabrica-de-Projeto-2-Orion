import streamlit as st
from api import getPatentes

itens = 10;
itens_por_pagina = 10;
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
        # Parametros do getPatentes(texto do input, quantidade total de patentes para serem buscadas)
        patentes = getPatentes(patente, itens)


        if not patentes:
            st.write("Nenhuma patente foi encontrada.")
        else:
            # Container de cards de patente
            with st.container():
                for patente in patentes[:itens_por_pagina]:
                    with st.container(horizontal_alignment="center", border=True):
                        titulo_patente = (f"{patente.get("title", "Título não informado")}")
                        #aqui eu usei o st.markdown pra conseguir personalizar o texto do titulo, aumentando ele e deixando em negrito. Da pra fazer isso usando a função "st.markdown" com HTML
                        st.markdown(
                            f"<h2 style = 'font-size: 28px; font-weight: bold; '>{titulo_patente}</h2>",
                            unsafe_allow_html=True
                        )
                        st.write(f"SN: {patente.get("pn", "PN não informado")}")
                        st.write(f"Autors: {patente.get("current_assignee", "Não informado")}")
                        #aqui eu vou colocar a publication date ("pbdt"), mas como ela estava em YYYYMMDD eu passei ela pra string e formatei com a função "formatar_data", puxando os números pelos índices
                        def formatar_data(data):
                            if not data:
                                return "Data não informada"
                            data = str(data)
                            return f"{data[6:8]}/{data[4:6]}/{data[0:4]}"
                        data_publicacao = formatar_data(patente.get("pbdt"))
                        st.write(f"Date: {data_publicacao}")

    elif enviado and not patente:
        st.write("Você precisa inserir alguma coisa na caixa de texto para buscar patentes")

if __name__ == "__main__": 
    main()
