FROM python:3.14
COPY --from=docker.io/astral/uv:0.13.0 /uv /uvx /bin/
WORKDIR /buscador_de_patentes/
COPY pyproject.toml uv.lock .python-version ./
COPY src/ ./src/
RUN uv sync
EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "src/buscador_de_patentes/main.py", "--server.address=0.0.0.0"]