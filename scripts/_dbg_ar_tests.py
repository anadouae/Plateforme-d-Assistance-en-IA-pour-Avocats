#!/usr/bin/env python3
import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=40)
_, o, _ = c.exec_command(
    "docker exec sanad-backend-1 python -m pytest tests/test_dictation_pipeline.py::test_repair_arabic_legal_lexicon tests/test_dictation_pipeline.py::test_repair_casablanca_phonetic -vv --tb=short 2>&1 | tail -40",
    timeout=60,
)
print(o.read().decode())
c.close()
