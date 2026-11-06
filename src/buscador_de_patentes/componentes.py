import streamlit as st
from api import getImagemPatente
from api import getDescricaoPatente

PAISES = {
    "US": "Estados Unidos",
    "EP": "Europa",
    "CN": "China",
    "JP": "Japão",
    "KR": "Coreia do Sul",
    "IN": "Índia",
    "BR": "Brasil",
    "CA": "Canadá",
    "AU": "Austrália",
    "RU": "Rússia",
}

def mostrar_card(patente, indice):
    with st.container(border=True):
        st.subheader(patente.get("title") or "Titulo não informado.")

        st.caption("Número da patente:")
        st.write(patente.get("pn") or "Não informado.")

        st.caption("Titular:")
        st.write(patente.get("current_assignee") or "Não informado.")

        # Botão que abre a área exclusiva dessa patente
        if st.button("Ver detalhes da patente ➔", key=f"btn_patente_{indice}"):
            st.session_state["patente_selecionada"] = patente
            st.rerun()


def mostrar_detalhes(patente):
    if st.button("⬅ Voltar para os resultados"):
        st.session_state["patente_selecionada"] = None
        st.rerun()

    st.divider()

    with st.container(border=True):
        st.header(patente.get("title") or "Título não informado")

        # Divide em 2 lados: Esquerda (informações) e Direita (imagem maior)
        col_esquerda, col_direita = st.columns([1.2, 1], gap="large")

        with col_esquerda:
            info1, info2 = st.columns(2)

            with info1:
                st.caption("Número da Patente (PN):")
                st.write(patente.get("pn") or patente.get("publication_number") or "Não informado.")

                st.caption("ID da Patente:")
                st.write(patente.get("patent_id") or "Não informado.")

                st.caption("Titular:")
                st.write(patente.get("current_assignee") or "Não informado.")

            with info2:
                sigla = patente.get("authority")
                nome_pais = PAISES.get(sigla, "Não informado.")
                st.caption("País de Publicação:")
                st.write(f"{sigla} - {nome_pais}" if sigla else "Não informado.")

                st.caption("Data de Publicação:")
                pbdt = patente.get("pbdt")
                if pbdt and len(str(pbdt)) == 8:
                    data_api = str(pbdt)
                    st.write(f"{data_api[6:]}/{data_api[4:6]}/{data_api[:4]}")
                else:
                    st.write("Não informado.")

            st.divider()
            st.caption("Descrição da Patente:")
            descricao = getDescricaoPatente(
                patent_id=patente.get("patent_id"),
                pn=patente.get("pn")
            )
            st.write(descricao or "Não informado.")


        with col_direita:
            st.caption("Figura da Patente:")
            url_imagem = getImagemPatente(
                patent_id=patente.get("patent_id"),
                pn=patente.get("pn"),
            )
            if url_imagem:
                st.image(url_imagem, use_container_width=True)
            else:
                st.write("Imagem não disponível.")