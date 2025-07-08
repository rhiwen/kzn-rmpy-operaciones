import os
from pathlib import Path
from dotenv import load_dotenv
from redminelib import Redmine

# ───────────────────────────────
# Cargar .env desde la raíz
# ───────────────────────────────
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

REDMINE_URL = os.getenv("REDMINE_URL")
API_KEY = os.getenv("REDMINE_API_KEY")
MAIL_DOMAIN = os.getenv("MAIL_DOMAIN", "@kaizen2b.com")

if not REDMINE_URL or not API_KEY:
    raise RuntimeError("Faltan REDMINE_URL o API_KEY en el .env")

# ───────────────────────────────
# Conexión Redmine
# ───────────────────────────────
redmine = Redmine(REDMINE_URL.rstrip("/"), key=API_KEY)

try:
    user = redmine.user.get("current")
    print(f"\n✅ Conectado a Redmine como: {user.login}\n")
except Exception as e:
    print(f"❌ Error al conectar a Redmine: {e}")
    exit(1)

# ───────────────────────────────
# Alias y grupos definidos
# ───────────────────────────────
ALIAS_TO_GROUP_IDS = {
    "desarrollo": [53],
    "data": [100],
    "tecnologia": [128],
    "consultores_tactica": [45],
}

# ───────────────────────────────
# Cargar usuarios por alias
# ───────────────────────────────
alias_map = {}

for alias, group_ids in ALIAS_TO_GROUP_IDS.items():
    alias_map[alias] = []
    for gid in group_ids:
        try:
            grupo = redmine.group.get(gid, include="users")
            print(f"📂 Grupo '{grupo.name}' (alias '{alias}', ID {gid})")
            if not grupo.users:
                print("   ⚠️  Grupo sin usuarios.")
                continue
            for u in grupo.users:
                try:
                    user = redmine.user.get(u.id)
                    email = f"{user.login}{MAIL_DOMAIN}"
                    alias_map[alias].append(email)
                    print(f"   • {email}")
                except Exception as ue:
                    print(f"   ❌ No se pudo acceder al usuario {u.id}: {ue}")
        except Exception as e:
            print(f"❌ Error al acceder al grupo {gid} (alias {alias}): {e}")
    print("-" * 60)

# ───────────────────────────────
# Mostrar resumen por alias
# ───────────────────────────────
print("\n📬 Resumen por alias:")

for alias, mails in alias_map.items():
    print(f"\n➡️ Alias '{alias}' — {len(mails)} usuarios:")
    for mail in sorted(mails):
        print(f"   • {mail}")
