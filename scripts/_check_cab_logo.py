import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('51.38.78.23', username='root', password='P@s$wiy.O0p', timeout=60)
cmd = '''
docker compose -f /opt/sanad/docker-compose.yml -f /opt/sanad/docker-compose.lexhub.yml --env-file /opt/sanad/.env.vps exec -T postgres psql -U lexhub -d lexhub -c "SELECT c.id, c.name, c.name_ar, c.logo_path, u.email FROM cabinets c JOIN users u ON u.cabinet_id = c.id WHERE u.email = 'demo@lexhub.space';"
'''
_, o, e = c.exec_command(cmd)
print("OUT:", o.read().decode())
print("ERR:", e.read().decode())
c.close()
