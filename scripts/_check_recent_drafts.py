import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('51.38.78.23', username='root', password='P@s$wiy.O0p', timeout=60)
cmd = '''
docker compose -f /opt/sanad/docker-compose.yml -f /opt/sanad/docker-compose.lexhub.yml --env-file /opt/sanad/.env.vps exec -T backend python -c "
from app.core.database import SessionLocal
from app.models import PlaidoirieDraft
db = SessionLocal()
drafts = db.query(PlaidoirieDraft).order_by(PlaidoirieDraft.updated_at.desc()).limit(3).all()
for d in drafts:
    print('DRAFT:', d.id, d.title)
    print('BODY HEAD (300 chars):', repr(d.body[:300]))
    print('---')
"
'''
_, o, e = c.exec_command(cmd)
print("OUT:\n", o.read().decode())
print("ERR:\n", e.read().decode())
c.close()
