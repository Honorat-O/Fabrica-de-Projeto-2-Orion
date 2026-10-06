import streamlit as st

def mostrar_card(patente):
    with st.container(border=True):
        st.subheader(patente.get("title") or "Titulo não informado.")

        st.caption("Número da patente:")
        st.write(patente.get("pn") or "Não informado.")

        st.caption("Titular:")
        st.write(patente.get("current_assignee") or "Não informado.")