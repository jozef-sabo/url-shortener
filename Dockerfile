FROM python:3.12-alpine AS base
LABEL authors="Jozef Sabo"

RUN apk add --no-cache \
        libpq-dev

WORKDIR /url-shortener

FROM base AS dependencies-builder

RUN apk add --no-cache \
        build-base \
        linux-headers

RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

RUN pip install uwsgi

COPY requirements.txt /url-shortener/

RUN pip install --no-cache -r requirements.txt

FROM base AS production

COPY --from=dependencies-builder /venv /venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 8000

RUN adduser -D shortener
USER shortener

COPY src /url-shortener/

CMD [ "uwsgi", "--ini", "uwsgi.ini" ]
