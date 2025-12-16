# OCI ARM Instance Factory 🏭

> Automator para provisionamento de instâncias Oracle Cloud Always Free (Ampere A1)

Este projeto é uma ferramenta de automação ("Sniper Bot") desenvolvida em Python para criar instâncias **ARM (Ampere A1 Compute)** na Oracle Cloud Infrastructure (OCI).

Objetivo: reduzir falhas "Out of Host Capacity" em regiões concorridas tentando criar instâncias dentro dos limites do Always Free, com um dashboard web para monitoramento.

---

## 🚀 Funcionalidades

- Persistência Inteligente: loop que tenta criar instâncias em todos os Availability Domains (ADs).
- Gestão de Capacidade: trata erros de capacidade e tenta outros ADs ou aguarda.
- Proteção contra Rate Limits: detecta `429 TooManyRequests` e faz cooldown de 5 minutos.
- Multi-nó: cria múltiplas instâncias sequencialmente.
- Dashboard Web:
  - Dark Mode com Bootstrap 5
  - Atualização em tempo real (AJAX)
  - Logs ao vivo
  - Botões Remotos: Parar e Reiniciar serviço
- Segurança: uso de `.env` para credenciais e logs rotacionados.

---

## 🛠️ Pré-requisitos

1. Conta Oracle Cloud com Always Free.
2. Usuário/API Key da OCI.
3. Servidor Linux (ex.: Ubuntu 20.04/22.04).
4. Python 3.10+ e pip.

---

## 📦 Instalação

1. Clonar o repositório:

```bash
git clone https://github.com/jean-amaral/oci-arm-instance-factory.git
cd oci-arm-instance-factory
```

2. Criar e ativar venv, instalar dependências:

```bash
sudo apt update && sudo apt install python3-venv -y
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Arquivo de configuração da OCI (`~/.oci/config`):

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaa...
fingerprint=xx:xx:xx...
tenancy=ocid1.tenancy.oc1..aaaa...
region=us-ashburn-1
key_file=/home/ubuntu/.oci/oci_api_key.pem
```

Crie o diretório `~/.oci` e coloque sua chave privada no caminho indicado em `key_file`.

---

## 🔧 Variáveis de ambiente (.env)

Crie `.env` na raiz com seus OCIDs e configurações. Exemplo:

```text
# --- Identidade e Rede ---
OCI_COMPARTMENT_ID=ocid1.tenancy.oc1..aaaa...
OCI_SUBNET_ID=ocid1.subnet.oc1.iad.aaaa...
SSH_KEY_PATH=/home/ubuntu/.ssh/id_rsa.pub

# --- Imagem ---
OCI_IMAGE_ID=ocid1.image.oc1.iad.aaaa...

# --- Tamanho da VM (Free Tier) ---
INSTANCE_SHAPE=VM.Standard.A1.Flex
INSTANCE_OCPUS=1
INSTANCE_MEMORY_GB=6
```

---

## 🖥️ Como Rodar (Modo Serviço / Produção)

Recomenda-se usar systemd para rodar o backend e o dashboard.

1. Serviço do Backend (`/etc/systemd/system/oci-factory.service`):

```ini
[Unit]
Description=OCI Instance Factory (Backend)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/oci-factory
EnvironmentFile=/home/ubuntu/oci-factory/.env
ExecStart=/home/ubuntu/oci-factory/venv/bin/python run_factory.py
StandardOutput=journal
StandardError=journal
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Serviço do Frontend (`/etc/systemd/system/oci-factory-web.service`):

```ini
[Unit]
Description=OCI Factory Web Dashboard
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/oci-factory
ExecStart=/home/ubuntu/oci-factory/venv/bin/uvicorn oci_factory.web.app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Permissões sudo para controle via web (`/etc/sudoers.d/oci-factory-web`):

```text
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart oci-factory.service
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop oci-factory.service
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/systemctl start oci-factory.service
```

4. Ativar serviços:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now oci-factory.service
sudo systemctl enable --now oci-factory-web.service
```

---

## 📊 Acessando o Dashboard

Abra: http://SEU_IP_DO_SERVIDOR:8000

O dashboard mostra status das tentativas, logs em tempo real e indica qual nó está sendo processado.

---

## ⚠️ Aviso Legal

Uso educacional/pessoal. O uso agressivo de APIs pode violar termos de serviço. Há mecanismos de proteção (cooldown), use por sua conta e risco.

---

## ✅ Sugestão Final

Adicione um `requirements.txt` na raiz com:

```text
oci
fastapi
uvicorn
jinja2
requests
```

Desenvolvido com ☕ e Python.