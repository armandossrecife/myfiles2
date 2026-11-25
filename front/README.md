# MyFiles: frontend (Flask)

Interface web do MyFiles. O usuário entra na conta, envia e visualiza imagens,
vídeos e áudios, escreve anotações, troca a foto de perfil e vê gráficos.

O frontend **não tem banco de dados**: todas as informações vêm da API do
backend. No Docker, ele roda sozinho no container `myfiles-front`.

- Aplicação: http://localhost:5001
- Verificação de saúde: http://localhost:5001/health

## Sumário

1. [Tecnologias](#tecnologias)
2. [Como o frontend conversa com o backend](#como-o-frontend-conversa-com-o-backend)
3. [Estrutura do código](#estrutura-do-código)
4. [Páginas](#páginas)
5. [Tratamento de erros](#tratamento-de-erros)
6. [Segurança](#segurança)
7. [Configuração](#configuração)
8. [Executando localmente](#executando-localmente)
9. [Executando no Docker](#executando-no-docker)
10. [Testes](#testes)

## Tecnologias

| Pacote | Uso |
|---|---|
| Flask 3.1 + Jinja2 | Rotas, sessão e templates |
| Flask-WTF | Proteção CSRF dos formulários |
| requests | Chamadas HTTP ao backend |
| Bootstrap 5.3 (CDN) | Layout e componentes visuais |
| plotly + pandas | Gráfico de linha do tempo (o plotly.js é servido pelo próprio frontend) |
| gunicorn | Servidor WSGI usado no container |

Versões exatas em [`requirements.txt`](requirements.txt).

## Como o frontend conversa com o backend

```
Navegador ──cookie de sessão──> Frontend (Flask) ──Authorization: Bearer <JWT>──> Backend (FastAPI)
```

1. **Login**: o frontend envia usuário e senha a `POST /login` do backend e
   guarda o `access_token` recebido na **sessão do Flask** (cookie assinado com
   `MY_SECRET_KEY`).
2. **Cada página** cria um `BackendClient` com esse token e faz as chamadas
   necessárias. O painel, por exemplo, chama perfil, anotações e arquivos.
3. **Mídias passam pelo frontend.** Imagens, vídeos, áudios e a foto de perfil
   aparecem no HTML com URLs do próprio frontend (`/arquivos/<id>/conteudo`,
   `/perfil/foto`). O frontend busca o conteúdo no backend com o token e o
   repassa em blocos de 64 KB (`web/routes/proxy.py`). Por isso o navegador
   nunca acessa o backend diretamente e o token nunca aparece no HTML.
4. **Uploads** também passam pelo frontend, que repassa o arquivo ao backend
   sem gravá-lo em disco.

## Estrutura do código

```
front/
├── main.py                  # ponto de entrada: app = create_app()
└── web/
    ├── __init__.py          # fábrica: CSRF, blueprints, tratadores de erro, filtros, /health
    ├── config.py            # Config lida das variáveis de ambiente
    ├── api.py               # BackendClient: todas as chamadas à API + exceções
    ├── sessao.py            # sessão do usuário e decorador login_required
    ├── routes/
    │   ├── auth.py          # login, cadastro, recuperação de senha, logout
    │   ├── dashboard.py     # / e /dashboard
    │   ├── notes.py         # anotações
    │   ├── files.py         # arquivos
    │   ├── profile.py       # perfil e foto
    │   ├── charts.py        # gráficos
    │   └── proxy.py         # repasse em streaming de conteúdo binário
    ├── templates/           # páginas Jinja2, todas herdam de base.html
    └── static/              # style.css, favicon.ico
```

- **`BackendClient`** é o único lugar que conhece as URLs da API. Ele adiciona
  o token, aplica o timeout e transforma as respostas de erro em exceções:
  `Unauthorized` (401), `BackendUnavailable` (sem conexão) e `BackendError`
  (demais erros, com o `detail` enviado pelo backend).
- A sessão HTTP do `requests` é compartilhada pela aplicação
  (`app.extensions["myfiles_http"]`). Isso reaproveita conexões e permite que
  os testes de integração a substituam.

## Páginas

| Rota | Método | Login | Página ou ação |
|---|---|---|---|
| `/` | GET | não | Redireciona para o painel ou para o login |
| `/login` | GET, POST | não | Entrar (aceita `?next=` apenas para caminhos internos) |
| `/register` | GET, POST | não | Criar conta |
| `/forgot-password` | GET | não | Orientação para recuperar a senha |
| `/logout` | POST | não | Sair |
| `/dashboard` | GET | sim | Painel: totais e itens recentes |
| `/notas` | GET, POST | sim | Lista e criação de anotações |
| `/notas/<id>/editar` | GET, POST | sim | Edição |
| `/notas/<id>/excluir` | POST | sim | Exclusão |
| `/arquivos` | GET, POST | sim | Lista e envio de arquivos |
| `/arquivos/<id>` | GET | sim | Visualização com o player certo (imagem, vídeo ou áudio) e botão de download |
| `/arquivos/<id>/conteudo` | GET | sim | Conteúdo repassado do backend |
| `/arquivos/<id>/excluir` | POST | sim | Exclusão |
| `/perfil` | GET | sim | Dados do usuário e troca de foto |
| `/perfil/foto` | GET, POST | sim | Foto atual (repassada) e envio de nova foto |
| `/graficos/tempo` | GET | sim | Linha do tempo (Plotly) |
| `/graficos/tarefas` | GET | sim | Tabela de tarefas |
| `/vendor/plotly.min.js` | GET | não | Biblioteca plotly.js |
| `/health` | GET | não | Saúde do container (não consulta o backend) |

## Tratamento de erros

| Situação | O que o usuário vê |
|---|---|
| Backend responde 401 (token expirado ou inválido) | Sessão limpa e volta ao login com aviso |
| Backend responde 400, 413 ou 422 em um formulário | Mensagem do backend no topo da página |
| Backend responde 403 ou 404 | Página de erro com o mesmo código |
| Backend fora do ar ou sem resposta | Página de erro 503 |
| Outro erro do backend | Página de erro 502 |
| Upload maior que o limite do frontend | Mensagem na página de arquivos (o arquivo nem chega ao backend) |
| Formulário sem token CSRF válido | Página de erro 400 |

## Segurança

- **CSRF**: todo formulário POST leva um `csrf_token` (Flask-WTF).
- **Cookie de sessão** `HttpOnly` e `SameSite=Lax`. Ele é assinado, mas não
  criptografado, então a chave `MY_SECRET_KEY` precisa ser secreta.
- **Exclusões e logout** só funcionam por POST.
- **Redirecionamento após o login** só aceita caminhos internos (sem open redirect).
- Os templates usam o escape automático do Jinja2, então o conteúdo das
  anotações não executa HTML.

## Configuração

| Variável | Padrão | Descrição |
|---|---|---|
| `MYFILES_BACKEND_URL` | `http://localhost:8000` | Endereço do backend. No Docker: `http://back:8000`. |
| `BACKEND_IP`, `BACKEND_PORT` | (vazio) | Alternativa a `MYFILES_BACKEND_URL`, mantida por compatibilidade |
| `MY_SECRET_KEY` | chave de desenvolvimento | Assina o cookie de sessão. **Troque em produção.** Trocar desloga todos os usuários. |
| `MYFILES_MAX_UPLOAD_MB` | `50` | Deve ser igual ao valor do backend |
| `MYFILES_BACKEND_TIMEOUT` | `30` | Timeout das chamadas ao backend (segundos) |
| `GUNICORN_WORKERS` | `2` | Processos do gunicorn (apenas no container) |

## Executando localmente

Com o backend já rodando em http://localhost:8000:

```bash
cd front
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export MYFILES_BACKEND_URL=http://localhost:8000
./exec.sh            # flask --app main run --host=0.0.0.0 --port=5001
```

## Executando no Docker

A imagem é definida em [`../docker/front.dockerfile`](../docker/front.dockerfile):

| Item | Valor |
|---|---|
| Imagem base | `python:3.12-slim` |
| Processo | `gunicorn --bind 0.0.0.0:5001 --workers $GUNICORN_WORKERS --timeout 120 main:app` |
| Usuário | `appuser` (uid 10001), sem privilégios de root |
| Porta | 5001 |
| Healthcheck | `GET /health` a cada 10 s |
| Dados persistentes | nenhum |

No Compose, o frontend só inicia depois que o backend está saudável
(`depends_on: condition: service_healthy`) e encontra o backend pelo nome do
serviço, `back`, na rede interna `myfiles-net`. O passo a passo está em
[`../docs/EXECUCAO_DOCKER.md`](../docs/EXECUCAO_DOCKER.md).

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

São 48 testes. O backend é simulado com `requests-mock`, e os testes verificam
tanto o que o frontend envia (URL, método, token, corpo) quanto o que ele exibe.

| Arquivo | O que cobre |
|---|---|
| `test_auth.py` | Login (sucesso, senha errada, campos vazios, backend fora do ar, `next`), cadastro, logout, sessão expirada, CSRF, configuração por variáveis |
| `test_notes.py` | Listagem, escape de HTML, criação, edição, exclusão, 404, exclusão só por POST |
| `test_files.py` | Listagem, envio, erros 400/413, limite do Flask, player por tipo de mídia, repasse do conteúdo, exclusão, erro 502 |
| `test_dashboard_e_perfil.py` | Painel, perfil, foto (repasse e envio), gráficos, plotly.js local, `/health`, página inexistente |

Os testes de integração com o backend real ficam em
[`../integracao/`](../integracao/).
