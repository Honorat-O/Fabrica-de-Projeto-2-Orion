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
                        st.write(f"{patente.get("title", "Título não informado")}")
                        st.write(f"{patente.get("pn", "PN não informado")}")
                        st.write(f"{patente.get("current_assignee", "Não informado")}")

    elif enviado and not patente:
        st.write("Você precisa inserir alguma coisa na caixa de texto para buscar patentes")

if __name__ == "__main__": 
    main()