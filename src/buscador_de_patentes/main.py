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
    
    if enviado:
        # Parametros do getPatentes(texto do input, quantidade total de patentes para serem buscadas)
        patentes = getPatentes(patente, itens)
        # Container de cards de patente
        with st.container():
            for i in range(itens_por_pagina):
                with st.container(key=i, horizontal_alignment="center", border=True):
                    st.write(f"{patentes[i]["title"]}")
                    st.write(f"{patentes[i]["pn"]}")
                    st.write(f"{patentes[i]["current_assignee"]}")
                    st.button("Ver mais", key=f"Botão {i}")

if __name__ == "__main__": 
    main()