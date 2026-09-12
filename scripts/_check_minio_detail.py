import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('51.38.78.23', username='root', password='P@s$wiy.O0p', timeout=60)
_, o, _ = c.exec_command("grep -E 'MINIO' /opt/sanad/.env.vps || echo 'NONE'")
print("MINIO in .env.vps:", o.read().decode())
_, o2, _ = c.exec_command("docker exec sanad-minio-1 printenv | grep -E 'MINIO_ROOT'")
print("sanad-minio-1 root:", o2.read().decode())
_, o3, _ = c.exec_command("docker exec sanad-backend-1 printenv | grep -E 'MINIO'")
print("sanad-backend-1 minio env:", o3.read().decode())
c.close()
