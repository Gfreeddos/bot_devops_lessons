#!/bin/bash

set -e

pg_basebackup -R -h $DB_HOST -U $POSTGRES_USER -D $PGDATA -p $DB_PORT -P || :

sed -i 's/^port=.*/port='$DB_REPL_PORT'/g' $PGDATA/postgresql.conf

bash /usr/local/bin/docker-entrypoint.sh -c config_file=$PGDATA/postgresql.conf -c hba_file=$PGDATA/pg_hba.conf
