FROM debian:sid
RUN echo 'deb http://mirrors.psu.ac.th/debian/ sid main contrib non-free' > /etc/apt/sources.list
# RUN echo 'deb http://mirror.kku.ac.th/debian/ sid main contrib non-free' >> /etc/apt/sources.list
RUN apt update --fix-missing && apt dist-upgrade -y
RUN apt install -y python3 python3-dev python3-pip python3-venv git locales swig xfonts-thai poppler-utils fontconfig npm
RUN sed -i '/th_TH.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG th_TH.UTF-8 
ENV LANGUAGE th_TH:en 
# ENV LC_ALL th_TH.UTF-8

RUN python3 -m venv /venv
ENV PYTHON=/venv/bin/python3
RUN $PYTHON -m pip install wheel poetry gunicorn

WORKDIR /app
COPY fonts /app/fonts
RUN mkdir -p /usr/share/fonts/opentype && cp -r fonts/* /usr/share/fonts/opentype/ && fc-cache -fv

COPY poetry.lock pyproject.toml /app/
RUN $PYTHON -m poetry config virtualenvs.create false && $PYTHON -m poetry install --no-interaction --only main

COPY viyyoor/web/static/package.json viyyoor/web/static/package-lock.json viyyoor/web/static/
RUN npm install --prefix viyyoor/web/static

COPY . /app
ENV VIYYOOR_SETTINGS=/app/viyyoor-production.cfg

# For brython
# RUN cd /app/kampan/web/static/brython; \
#     for i in $(ls -d */); \
#     do \
#     cd $i; \
#     python3 -m brython --make_package ${i%%/}; \
#     mv *.brython.js ..; \
#     cd ..; \
#     done
