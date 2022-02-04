FROM debian:sid
RUN echo 'deb http://mirrors.psu.ac.th/debian/ sid main contrib non-free' > /etc/apt/sources.list
# RUN echo 'deb http://mirror.kku.ac.th/debian/ sid main contrib non-free' >> /etc/apt/sources.list
RUN apt update --fix-missing && apt dist-upgrade -y
RUN apt install -y python3 python3-dev python3-pip python3-venv git locales swig xfonts-thai poppler-utils fontconfig npm
RUN sed -i '/th_TH.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG th_TH.UTF-8 
ENV LANGUAGE th_TH:en 
# ENV LC_ALL th_TH.UTF-8
COPY . /app
WORKDIR /app

RUN mkdir -p /usr/share/fonts/opentype && cp -r fonts/* /usr/share/fonts/opentype/ && fc-cache -fv
RUN npm install --prefix viyyoor/web/static

ENV VIYYOOR_SETTINGS=/app/viyyoor-production.cfg

RUN ln -s $(command -v python3) /usr/bin/python
RUN pip3 install poetry uwsgi
RUN poetry config virtualenvs.create false && poetry install --no-interaction
ENV PYTHONPATH $(pwd):/usr/lib/python3.9/site-packages:$PYTHONPATH

# For brython
# RUN cd /app/viyyoor/web/static/brython; \
#     for i in $(ls -d */); \
#     do \
#     cd $i; \
#     python3 -m brython --make_package ${i%%/}; \
#     mv *.brython.js ..; \
#     cd ..; \
#     done
