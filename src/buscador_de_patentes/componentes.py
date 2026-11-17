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

        pn = patente.get("pn") or patente.get("publication_number")

        # Garante que dicionário de patentes salvas existe (segurança extra)
        if "patentes_salvas" not in st.session_state:
            st.session_state.patentes_salvas = {}

        # Verifica se patente já foi adicionada pelo seu "pn"
        ja_adicionada = pn in st.session_state.patentes_salvas

        # Cria botão com chave única, bloqueio e tooltip
        if st.button(
            "Adicionar Patente",
            key=f"btn_add_card{indice}",
            disabled=ja_adicionada,
            help="Patente já adicionada" if ja_adicionada else None
        ):
            st.session_state.patentes_salvas[pn] = patente
            st.rerun()
        

def montar_linha_planilha(patente, descricao):
    numero_da_patente = patente.get("pn") or patente.get("publication_number")
    titulo = patente.get("title")
    titular = patente.get("current_assignee")
    sigla_pais = patente.get("authority")

    data_publicacao = patente.get("pbdt")
    if data_publicacao and len(str(data_publicacao)) == 8:
        data_api = str(data_publicacao)
        data_publicacao = (f"{data_api[6:]}/{data_api[4:6]}/{data_api[:4]}")

    patente_id = patente.get("patent_id")

    resumo = descricao

    dicionario = {"Número da patente": numero_da_patente,
                  "Título": titulo,
                  "Titular": titular,
                  "País": sigla_pais,
                  "Data de publicação": data_publicacao,
                  "ID": patente_id,
                  "Resumo": resumo}

    return dicionario

def mostrar_detalhes(patente):
    if st.button("⬅ Voltar para os resultados"):
        st.session_state["patente_selecionada"] = None
        st.rerun()

    pn = patente.get("pn") or patente.get("publication_number")

    if "patentes_salvas" not in st.session_state:
        st.session_state["patentes_salvas"] = {}

    ja_adicionada = pn in st.session_state["patentes_salvas"]

    if st.button(
        "Adicionar Patente",
        key=f"btn_add_detalhes_{pn}",
        disabled=ja_adicionada,
        help="Patente já adicionada" if ja_adicionada else None
    ):
        st.session_state["patentes_salvas"][pn] = patente
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