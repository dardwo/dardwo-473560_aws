import os
import time
from hcloud import Client
from hcloud.images.domain import Image
from hcloud.server_types.domain import ServerType
from hcloud.locations.domain import Location
from dotenv import load_dotenv

# 1. Ładowanie konfiguracji
load_dotenv()
TOKEN = os.getenv("HCLOUD_TOKEN")
if not TOKEN:
    print("BŁĄD: Brak tokenu w pliku .env")
    exit(1)

client = Client(token=TOKEN)
LABEL = "test-vscode" # 2. Etykieta, po której potem łatwo usuniemy serwer

print(f"--- Rozpoczynam symulację sprawdzania Zadania 3.4 ---")

cloud_init_path = "templates/cloud_init_vscode.yaml"
try:
    with open(cloud_init_path, "r") as f:
        user_data = f.read()
    print(f"Załadowano plik: {cloud_init_path}")
except FileNotFoundError:
    print(f"BŁĄD: Nie znaleziono pliku {cloud_init_path}!")
    exit(1)

# 3. Obsługa klucza SSH (wymagane przez Hetzner do utworzenia VM)
ssh_key_name = f"dardwo-pzc-ssh-key"
if existing_key := client.ssh_keys.get_by_name(ssh_key_name):
    ssh_key = existing_key
else:
    try:
        with open(os.path.expanduser("~/.ssh/id_rsa.pub"), "r") as f:
            pub_key = f.read()
        ssh_key = client.ssh_keys.create(name=ssh_key_name, public_key=pub_key)
    except FileNotFoundError:
        print("BŁĄD: Nie znaleziono klucza ~/.ssh/id_rsa.pub. Wygeneruj go komendą: ssh-keygen")
        exit(1)

# 4. Tworzenie serwera CPX11
print("Tworzenie serwera CPX11...")
try:
    response = client.servers.create(
        name=f"{LABEL}-vm",
        server_type=ServerType("cpx11"),
        image=Image(name="ubuntu-24.04"),
        location=Location("hel1"),
        ssh_keys=[ssh_key],
        user_data=user_data,
        labels={"creator": LABEL}
    )
    
    server = response.server
    response.action.wait_until_finished()
    
    server = client.servers.get_by_id(server.id)
    public_ip = server.public_net.ipv4.ip
    
    print("\n--- SUKCES! Serwer został utworzony ---")
    print(f"IP Serwera: {public_ip}")
    print("Instalacja Dockera i VS Code trwa zazwyczaj około 2-3 minuty.")
    print(f"Sprawdź działanie pod adresem: http://{public_ip}:8080")
    print("Hasło (jeśli nie zmieniłaś w YAML): student")
    
except Exception as e:
    print(f"Wystąpił błąd podczas tworzenia serwera: {e}")