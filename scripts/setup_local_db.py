"""Create an isolated PostgreSQL cluster. Never overwrite an existing .env or cluster."""
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / '.local'
BIN = LOCAL / 'pgsql' / 'bin'
DATA = LOCAL / 'pgdata'

def main():
    import psycopg
    from psycopg import sql
    if (ROOT / '.env').exists() or DATA.exists():
        raise SystemExit('Ya existe .env o pgdata; no se modifica. Revisa la configuración existente.')
    admin_password = secrets.token_urlsafe(36)
    app_password = secrets.token_urlsafe(36)
    password_file = LOCAL / 'init-password.tmp'
    password_file.write_text(admin_password, encoding='utf-8')
    try:
        subprocess.run([str(BIN / 'initdb.exe'), '-D', str(DATA), '-U', 'postgres',
                        '--auth=scram-sha-256', '--encoding=UTF8', '--locale=C',
                        '--pwfile', str(password_file)], check=True)
    finally:
        password_file.unlink(missing_ok=True)
    with (DATA / 'postgresql.conf').open('a', encoding='utf-8') as config:
        config.write("\nlisten_addresses = '127.0.0.1'\nport = 5433\n")
    (LOCAL / 'postgres-admin.env').write_text('POSTGRES_PASSWORD=' + admin_password + '\n', encoding='utf-8')
    subprocess.run([str(BIN / 'pg_ctl.exe'), '-D', str(DATA), '-l', str(LOCAL / 'postgres.log'), '-w', 'start'], check=True)
    with psycopg.connect(host='127.0.0.1', port=5433, dbname='postgres', user='postgres', password=admin_password, autocommit=True) as connection:
        connection.execute(sql.SQL('CREATE ROLE manovision LOGIN CREATEDB PASSWORD {}').format(sql.Literal(app_password)))
        connection.execute('CREATE DATABASE manovision OWNER manovision')
    (ROOT / '.env').write_text(
        'DEBUG=1\nSECRET_KEY=' + secrets.token_urlsafe(50) + '\nALLOWED_HOSTS=127.0.0.1,localhost\n'
        'POSTGRES_DB=manovision\nPOSTGRES_USER=manovision\nPOSTGRES_PASSWORD=' + app_password +
        '\nPOSTGRES_HOST=127.0.0.1\nPOSTGRES_PORT=5433\n', encoding='utf-8')
    print('PostgreSQL local preparado en 127.0.0.1:5433. Credenciales guardadas sin mostrarlas.')

if __name__ == '__main__':
    main()
