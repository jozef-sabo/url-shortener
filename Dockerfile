FROM alpine:latest

RUN apk add --update --no-cache wget gcc cmake make readline-dev ncurses-dev openssl-dev tk-dev gdbm-dev libc-dev bzip2-dev libffi-dev zlib-dev libpq-dev

RUN wget -c https://www.python.org/ftp/python/3.12.4/Python-3.12.4.tar.xz \
    && tar -Jxvf Python-3.12.4.tar.xz \
    && cd Python-3.12.4 \
    && ./configure --enable-optimizations --prefix=/usr/local LDFLAGS="-Wl,-rpath /usr/local/lib" \
    && make -j4 && make install \
    && cd .. \
    && rm -rf ./Python-3.12.4 \
    && rm -f ./Python-3.12.4.tar.xz \
    && python3 --version

WORKDIR /url-shortener

COPY requirements.txt /url-shortener/

RUN python3 -m ensurepip  \
    && pip3 install --no-cache -r requirements.txt

RUN pip3 install uwsgi

EXPOSE 8000

RUN adduser -D shortener
USER shortener

COPY src /url-shortener/

CMD [ "uwsgi", "--ini", "uwsgi.ini" ]
