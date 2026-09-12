import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('51.38.78.23', username='root', password='P@s$wiy.O0p', timeout=60)
cmd = '''
grep -i minio /opt/sanad/.env.vps || echo "No minio in .env.vps"
docker exec sanad-minio-1 printenv | grep -i minio
'''
_, o, e = c.exec_command(cmd)
print("OUT:\n", o.read().decode())
c.close()
