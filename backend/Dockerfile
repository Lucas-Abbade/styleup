FROM python:3.12-slim

WORKDIR /app

# Dependências de sistema exigidas por Pillow e onnxruntime
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-visao.txt ./
# ARG COM_VISAO=true instala torch/rembg (~2 GB). Deixe false para uma imagem leve.
ARG COM_VISAO=true
RUN pip install --no-cache-dir -r requirements.txt \
 && if [ "$COM_VISAO" = "true" ]; then \
      pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
      pip install --no-cache-dir transformers rembg onnxruntime; \
    fi

COPY app ./app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s \
  CMD python -c "import httpx;httpx.get('http://localhost:8000/saude').raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
