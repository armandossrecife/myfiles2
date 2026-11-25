# Docker

- `back.dockerfile`: imagem do backend + banco SQLite (dados no volume `/data`)
- `front.dockerfile`: imagem do frontend (gunicorn)

O passo a passo completo para executar a aplicação está em
[`../docs/EXECUCAO_DOCKER.md`](../docs/EXECUCAO_DOCKER.md). Em resumo, na raiz
do repositório:

```bash
cp .env.example .env        # opcional: ajuste chaves e usuário inicial
docker compose up --build -d
# http://localhost:5001
```
