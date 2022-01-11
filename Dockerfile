FROM python:3.7.11 AS base
WORKDIR /usr/src/app
COPY ./src/requirements.txt ./
RUN pip install -U --no-cache-dir pip setuptools wheel && \
    pip install --no-cache-dir Cython && \ 
    pip install --no-cache-dir -r requirements.txt 
STOPSIGNAL SIGINT

FROM base AS prod
COPY ./src ./

FROM base as debug
RUN pip --no-cache-dir install ptvsd
COPY ./src ./
CMD ["python", "-m", "ptvsd", "--host" , "0.0.0.0" , "--port", "5678", "--wait", "client.py" , "-config", "configfile.yml" ]

