
# Dedicated Server (Headless)

Este diretório contém um **servidor dedicado** sem pygame, pronto para subir em providers (ex.: Koyeb/Railway/Fly/Render).

## Executar local
```bash
python DedicatedServer/server_main.py
# usa a porta do config.py (7777) ou PORT do ambiente
PORT=9000 python DedicatedServer/server_main.py
```

## Docker
```bash
docker build -t hypershooter-server -f DedicatedServer/Dockerfile .
docker run -p 7777:7777 -e PORT=7777 hypershooter-server
```

## Koyeb (ou similar)
1. Crie um novo serviço a partir deste repositório.
2. Defina a variável de ambiente **PORT=7777** (ou a porta que preferir).
3. Aponte o comando de start para:
```
python server_main.py
```
4. **Importante**: habilite **TCP** na porta exposta pelo provider (alocada automaticamente ou 7777).

Os clientes se conectam usando o **IP/host público e porta** fornecidos pelo provider.
