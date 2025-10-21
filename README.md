
# HyperShooter Dedicated Server

Servidor dedicado (sem pygame) para o jogo HyperShooter.

## Rodar local
```bash
python server_main.py               # usa porta do config.py (7777)
PORT=9000 python server_main.py     # porta customizada
```

## Docker
```bash
docker build -t hypershooter-server .
docker run -p 7777:7777 -e PORT=7777 hypershooter-server
```

## Deploy na Koyeb
1. Crie um repositório Git com **estes arquivos na raiz**: `config.py`, `common.py`, `server.py`, `server_main.py`, `Dockerfile`, `Procfile`.
2. Na Koyeb, crie um serviço a partir do GitHub.
3. Variável de ambiente: **PORT=7777**.
4. O Dockerfile já copia tudo e inicializa com `python server_main.py`.
5. O serviço expõe a porta TCP pública; use esse **host:porta** no cliente.
