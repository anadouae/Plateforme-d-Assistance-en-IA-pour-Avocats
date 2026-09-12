# Accès Adminer LexHub (ops)

Adminer **n’est plus** public sur HTTPS.

## Accès sécurisé

1. Tunnel SSH :
```powershell
python scripts\open_adminer_tunnel.py
```
   ou double-clic `Ouvrir_Adminer.bat`

2. Navigateur : **http://127.0.0.1:8088**

3. Login SQL (après Vague B) :
   - Système : PostgreSQL
   - Serveur : **postgres**
   - Utilisateur : **lexhub**
   - Mot de passe : voir fichier Bureau `LexHub_DB_credentials.txt` (prod)
   - Base : **lexhub**

En local Docker par défaut : user/db `lexhub` / `lexhub_secret`.
