FROM dpage/pgadmin4:7.2

USER root

ARG DB_USER
ARG DB_HOST
ARG DB_PORT
ARG DB_DATABASE

ENV DB_USER=$DB_USER
ENV DB_HOST=$DB_HOST
ENV DB_PORT=$DB_PORT
ENV DB_DATABASE=$DB_DATABASE

ARG DB_REPL_USER
ARG DB_REPL_HOST
ARG DB_REPL_PORT

ENV DB_REPL_USER=$DB_REPL_USER
ENV DB_REPL_HOST=$DB_REPL_HOST
ENV DB_REPL_PORT=$DB_REPL_PORT

COPY ./servers.json /pgadmin4/servers.json

RUN apk add --upgrade --no-cache sed

RUN sed -i "s/DB_HOST/${DB_HOST}/g" /pgadmin4/servers.json
RUN sed -i "s/DB_USER/${DB_USER}/g" /pgadmin4/servers.json
RUN sed -i "s/DB_PORT/${DB_PORT}/g" /pgadmin4/servers.json
RUN sed -i "s/DB_DATABASE/${DB_DATABASE}/g" /pgadmin4/servers.json
RUN sed -i "s/DB_REPL_HOST/${DB_REPL_HOST}/g" /pgadmin4/servers.json
RUN sed -i "s/DB_REPL_PORT/${DB_REPL_PORT}/g" /pgadmin4/servers.json
RUN sed -i "s/DB_REPL_USER/${DB_REPL_USER}/g" /pgadmin4/servers.json

