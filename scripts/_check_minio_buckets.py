import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('51.38.78.23', username='root', password='P@s$wiy.O0p', timeout=60)
cmd = '''
docker compose -f /opt/sanad/docker-compose.yml -f /opt/sanad/docker-compose.lexhub.yml --env-file /opt/sanad/.env.vps exec -T backend python -c "
from minio import Minio
client = Minio('minio:9000', access_key='sanad_minio', secret_key='sanad_minio_secret', secure=False)
buckets = client.list_buckets()
print('Buckets:', [b.name for b in buckets])
for b in buckets:
    objs = list(client.list_objects(b.name, recursive=True))
    print(f'Bucket {b.name} has {len(objs)} objects:')
    for o in objs[:10]:
        print('  -', o.object_name)
"
'''
_, o, e = c.exec_command(cmd)
print("OUT:\n", o.read().decode())
print("ERR:\n", e.read().decode())
c.close()
