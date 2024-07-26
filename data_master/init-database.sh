#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE ROLE $DB_REPL_USER WITH REPLICATION LOGIN PASSWORD '$DB_REPL_PASSWORD';
	CREATE TABLE emails(
		ID SERIAL PRIMARY KEY,
		email VARCHAR (100) NOT NULL,
		id_user VARCHAR (30));
        CREATE TABLE phones(
                ID SERIAL PRIMARY KEY,
                phone VARCHAR (100) NOT NULL,
                id_user VARCHAR (30));
EOSQL


sed -i 's/^#port.*/port='$PG_PORT'/g' $PGDATA/postgresql.conf
sed -i 's/^#archive_mode.*/archive_mode='on'/g' $PGDATA/postgresql.conf
sed -i "s/^#archive_command.*/archive_command='cp %p \/oracle\/pg_data\/archive\/%f'/g" $PGDATA/postgresql.conf
sed -i 's/^#max_wal_senders.*/max_wal_senders='10'/g' $PGDATA/postgresql.conf
sed -i 's/^#wal_level.*/wal_level='replica'/g' $PGDATA/postgresql.conf
sed -i 's/^#wal_log_hints.*/wal_log_hints='on'/g' $PGDATA/postgresql.conf
sed -i 's/^#log_replication_commands.*/log_replication_commands='on'/g' $PGDATA/postgresql.conf

echo "host    replication     $DB_REPL_USER       all           md5" >> $PGDATA/pg_hba.conf
