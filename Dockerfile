ARG IMAGE=intersystemsdc/irishealth-community
ARG IMAGE=intersystemsdc/iris-community
FROM $IMAGE

WORKDIR /home/irisowner/dev

ARG TESTS=0
ARG MODULE="iris-python-template"
ARG NAMESPACE="USER"


# create Python env
## Embedded Python environment
ENV IRISNAMESPACE "IRISAPP"
# ENV PYTHON_PATH=/usr/irissys/bin/
# ENV PYTHON_PATH=/usr/irissys/mgr/python/
ENV PYTHONPATH=/usr/irissys/mgr/python/
ENV PATH "/usr/irissys/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/irisowner/bin:/home/irisowner/.local/bin"
# ENV LIBRARY_PATH=${ISC_PACKAGE_INSTALLDIR}/bin:${LIBRARY_PATH}
## Start IRIS

 # copy the python code to the IRIS python home
COPY ./python /usr/irissys/mgr/python/irisapp

RUN --mount=type=bind,src=.,dst=. \
pip3 install -r requirements.txt && \
python3 -m spacy download pt_core_news_sm && \
python3 -m spacy download en_core_web_sm && \
iris start IRIS && \
iris merge IRIS merge.cpf && \
iris session IRIS < iris.script && \
# irispython iris_script.py && \
iris stop IRIS quietly
