# OCI ARM Instance Factory 🏭

> **Automator para provisionamento de instâncias Oracle Cloud Always Free (Ampere A1)**

Este projeto é uma ferramenta de automação robusta ("Sniper Bot") desenvolvida em Python para criar instâncias **ARM (Ampere A1 Compute)** na Oracle Cloud Infrastructure (OCI). 

O objetivo principal é superar o erro comum de **"Out of Host Capacity"** em regiões muito concorridas, tentando persistentemente criar as instâncias dentro dos limites do nível gratuito (Always Free), com uma interface web moderna para monitoramento e controle.

---

## 🚀 Funcionalidades

* **Persistência Inteligente:** Loop contínuo que tenta criar instâncias em todos os Domínios de Disponibilidade (ADs) da sua região.
* **Gestão de Capacidade:** Lida automaticamente com erros de capacidade, tentando o próximo AD ou aguardando.
* **Proteção Anti-Ban (Rate Limit):** Detecta erros `429 TooManyRequests` e entra em modo de espera (Cooldown) de 5 minutos para evitar bloqueios da API.
* **Multi-Nó:** Configurado para tentar criar múltiplas instâncias (ex: Instância-1 e Instância-2) sequencialmente.
* **Dashboard Web Moderno:**
    * Interface Dark Mode com Bootstrap 5.
    * Atualização em tempo real (AJAX) sem refresh de página.
    * Logs ao vivo no navegador.
    * Controles Web: Botões para **Parar** e **Reiniciar** o serviço remotamente.
* **Seguro:** Credenciais separadas em arquivo `.env` (não versionado) e logs com rotação automática para não encher o disco.

---

## 🛠️ Pré-requisitos

1.  **Conta Oracle Cloud:** Com acesso ao nível Always Free.
2.  **Usuário/API Key:** Você precisa gerar um par de chaves API no painel da Oracle.
3.  **Servidor Linux:** Recomendado Ubuntu 20.04 ou 22.04 (pode ser uma instância AMD micro gratuita).
4.  **Python 3.10+** e `pip`.

---

## 📦 Instalação

### 1. Clonar o Repositório

```bash
git clone [https://github.com/jean-amaral/oci-arm-instance-factory.git](https://github.com/jean-amaral/oci-arm-instance-factory.git)
cd oci-arm-instance-factory
2. Configurar Ambiente Virtual
Bash

# Instala o venv se não tiver
sudo apt update && sudo apt install python3-venv -y

# Cria o ambiente
python3 -m venv venv

# Ativa o ambiente
source venv/bin/activate

# Instala as dependências
pip install oci fastapi uvicorn jinja2
⚙️ Configuração
1. Configuração OCI (~/.oci/config)
O script usa o arquivo padrão de configuração da OCI. Crie o diretório e o arquivo:

Bash

mkdir -p ~/.oci
nano ~/.oci/config
Cole suas credenciais (obtidas no console da Oracle em User Settings > API Keys):

Ini, TOML

[DEFAULT]
user=ocid1.user.oc1..aaaa...
fingerprint=xx:xx:xx...
tenancy=ocid1.tenancy.oc1..aaaa...
region=us-ashburn-1
key_file=/home/ubuntu/.oci/oci_api_key.pem
Nota: Certifique-se de colocar seu arquivo .pem (chave privada) no caminho indicado em key_file.

2. Variáveis de Ambiente (.env)
Crie o arquivo .env na raiz do projeto para definir o que você quer criar:

Bash

nano .env
Conteúdo modelo (substitua pelos seus OCIDs):

Ini, TOML

# --- Identidade e Rede ---
# Geralmente o Tenancy ID serve como Compartment ID no Free Tier
OCI_COMPARTMENT_ID=ocid1.tenancy.oc1..aaaa... 
OCI_SUBNET_ID=ocid1.subnet.oc1.iad.aaaa...
SSH_KEY_PATH=/home/ubuntu/.ssh/id_rsa.pub

# --- Configurações da Instância ---
# ID da Imagem (ex: Ubuntu 22.04 ARM)
OCI_IMAGE_ID=ocid1.image.oc1.iad.aaaa...

# --- Tamanho da VM (Free Tier permite até 4 OCPU / 24GB total) ---
# Exemplo para criar 2 instâncias pequenas:
INSTANCE_SHAPE=VM.Standard.A1.Flex
INSTANCE_OCPUS=1
INSTANCE_MEMORY_GB=6
🖥️ Como Rodar (Modo Serviço / Produção)
Para que o robô rode 24/7 e inicie com o sistema, usamos o systemd.

1. Serviço do Backend (O Robô)
Crie o arquivo /etc/systemd/system/oci-factory.service:

Ini, TOML

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
2. Serviço do Frontend (O Dashboard)
Crie o arquivo /etc/systemd/system/oci-factory-web.service:

Ini, TOML

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
3. Permissões para Controle Web
Para que os botões "Parar/Reiniciar" funcionem na web, o usuário precisa de permissão sudo específica.

Bash

sudo nano /etc/sudoers.d/oci-factory-web
Adicione:

Plaintext

ubuntu ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart oci-factory.service
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop oci-factory.service
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/systemctl start oci-factory.service
4. Ativar tudo
Bash

sudo systemctl daemon-reload
sudo systemctl enable --now oci-factory.service
sudo systemctl enable --now oci-factory-web.service
📊 Acessando o Dashboard
Abra seu navegador e acesse: http://SEU_IP_DO_SERVIDOR:8000

Você verá:

Status de cada tentativa.

Logs em tempo real.

Indicação visual (Card pulsando) de qual nó está sendo processado.

⚠️ Aviso Legal
Este projeto é para fins educacionais e de automação pessoal. O uso agressivo de APIs pode violar os termos de serviço de alguns provedores. O código possui travas de segurança (Cooldown em erro 429) para mitigar riscos, mas use por sua conta e risco.

Desenvolvido com ☕ e Python.


### Sugestão Final
No seu repositório GitHub, certifique-se de criar também um arquivo `requirements.txt` com o seguinte conteúdo, para facilitar a instalação de quem baixar:

```text
oci
fastapi
uvicorn
jinja2
requests