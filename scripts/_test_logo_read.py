import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('51.38.78.23', username='root', password='P@s$wiy.O0p', timeout=60)
cmd = '''
docker compose -f /opt/sanad/docker-compose.yml -f /opt/sanad/docker-compose.lexhub.yml --env-file /opt/sanad/.env.vps exec -T backend python -c "
from app.core.database import SessionLocal
from app.models import Cabinet, User
from app.services.object_storage import read_file, _get_minio

db = SessionLocal()
user = db.query(User).filter(User.email == 'demo@lexhub.space').first()
cab = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
print('cab:', cab.name, 'logo_path:', cab.logo_path)
client = _get_minio()
print('minio client:', bool(client))
if client:
    buckets = [b.name for b in client.list_buckets()]
    print('buckets in minio:', buckets)
if cab.logo_path:
    try:
        data = read_file(cab.logo_path)
        print('read_file success, bytes:', len(data))
    except Exception as e:
        print('read_file ERROR:', type(e), e)
"
'''
_, o, e = c.exec_command(cmd)
print("OUT:\n", o.read().decode())
print("ERR:\n", e.read().decode())
c.close()
