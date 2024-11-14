FROM continuumio/miniconda3

WORKDIR /src/datapi

COPY environment.yml /src/datapi/

RUN conda install -c conda-forge gcc python=3.11 \
    && conda env update -n base -f environment.yml

COPY . /src/datapi

RUN pip install --no-deps -e .
