#!/usr/bin/env bash
# Testa as migrações num Postgres local descartável (não toca no Supabase).
#
#   ./supabase/testes/rodar.sh
#
# Requer os binários do PostgreSQL 15+ (initdb, pg_ctl, psql) no PATH ou em
# /usr/lib/postgresql/<versão>/bin. O que é verificado:
#   1. 0001–0005 aplicam em ordem sobre um banco com dados antigos (legado.sql);
#   2. 0003–0005 podem ser executadas de novo sem erro;
#   3. os casos de casos.sql (código CLO, RLS, métricas, atomicidade, LGPD);
#   4. os scripts de reverter/ desfazem 0005, 0004 e 0003, e elas reaplicam.
set -euo pipefail

AQUI="$(cd "$(dirname "$0")" && pwd)"
MIGRACOES="$AQUI/../migrations"
BIN="$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | sort -V | tail -1 || true)"
[ -n "$BIN" ] && PATH="$BIN:$PATH"
command -v initdb >/dev/null || { echo "PostgreSQL não encontrado (initdb)"; exit 2; }

DADOS="$(mktemp -d)"; PORTA="${PORTA:-54329}"
COMO=""; [ "$(id -u)" = "0" ] && { chown postgres "$DADOS"; chmod 755 "$AQUI" "$MIGRACOES"; COMO="runuser -u postgres --"; }
encerrar() { $COMO pg_ctl -D "$DADOS" -m immediate stop >/dev/null 2>&1 || true; rm -rf "$DADOS"; }
trap encerrar EXIT

$COMO initdb -D "$DADOS" -U postgres -A trust >/dev/null
$COMO pg_ctl -D "$DADOS" -o "-p $PORTA -c listen_addresses='' -k $DADOS" -w start >/dev/null
sql() { $COMO psql -X -q -v ON_ERROR_STOP=1 -h "$DADOS" -p "$PORTA" -U postgres -d postgres "$@"; }

echo "1/4 aplicando 0001-0005 sobre dados antigos"
sql -f "$AQUI/stub_supabase.sql"
sql -f "$MIGRACOES/0001_schema.sql" -f "$MIGRACOES/0002_rls.sql"
sql -f "$AQUI/legado.sql"
for m in 0003 0004 0005; do sql -f "$MIGRACOES"/${m}_*.sql; done

echo "2/4 reaplicando 0003-0005 (idempotência)"
for m in 0003 0004 0005; do sql -f "$MIGRACOES"/${m}_*.sql; done

echo "3/4 casos de teste"
sql -f "$AQUI/casos.sql"

echo "4/4 revertendo e reaplicando"
for m in 0005 0004 0003; do sql -f "$MIGRACOES/reverter/${m}_reverter.sql"; done
for m in 0003 0004 0005; do sql -f "$MIGRACOES"/${m}_*.sql; done

echo "OK: migrações válidas"
