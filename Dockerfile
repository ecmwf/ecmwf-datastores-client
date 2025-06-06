FROM continuumio/miniconda3

WORKDIR /src/ecmwf-datastores-client

COPY environment.yml /src/ecmwf-datastores-client/

RUN conda install -c conda-forge gcc python=3.11 \
    && conda env update -n base -f environment.yml

COPY . /src/ecmwf-datastores-client

RUN pip install --no-deps -e .
