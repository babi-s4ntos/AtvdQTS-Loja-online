# ARENA WEAR — Loja virtual e painel administrativo

E-commerce da **ARENA WEAR**, integrado ao sistema de gestão existente, desenvolvido com **Python, FastAPI e SQLite**.

O projeto reúne a loja virtual pública e o painel administrativo em uma única aplicação. O painel de gestão permanece em `app/static/index.html`, enquanto a loja virtual está localizada em `app/static/store/`.

**Nome do projeto:** ARENA WEAR  
**Segmento:** Streetwear e moda urbana.
## 1. Requisitos

- Python 3.12 ou superior.
- [uv](https://docs.astral.sh/uv/).
- Conta de vendedor no Mercado Pago e aplicativo de integração.
- Conta e aplicativo no Melhor Envio com token de API.
- Hospedagem com HTTPS e domínio público para recebimento dos webhooks de pagamento.

## 2. Instalação e execução local

Abra o PowerShell na pasta que contém o arquivo `pyproject.toml`.

### Instalar dependências

```powershell
uv sync --extra dev
```

### Configurar variáveis de ambiente

```powershell
Copy-Item .env.example .env
```

Edite o arquivo `.env` para configurar as chaves, credenciais e dados da loja.

### Iniciar a aplicação

```powershell
uv run uvicorn app.main:app --reload
```

### Endereços locais

| Recurso | Endereço |
|---|---|
| Loja virtual | http://127.0.0.1:8000/ |
| Painel administrativo | http://127.0.0.1:8000/admin |
| Documentação da API | http://127.0.0.1:8000/docs |

Para desenvolvimento, a variável `SEED_DEMO_DATA=true` permite criar produtos de demonstração caso o banco esteja vazio.

Em produção, utilize `APP_ENV=production` e `SEED_DEMO_DATA=false`, cadastrando os produtos reais pelo painel administrativo.

O banco de dados existente recebe migrações aditivas com `ALTER TABLE`, preservando as tabelas administrativas.

---

## 3. Configuração das integrações

Copie `.env.example` para `.env` e configure as variáveis necessárias.

**Importante:** o arquivo `.env` está no `.gitignore`. Nunca publique tokens, senhas ou credenciais no GitHub.

### 3.1 Mercado Pago — Pix e cartão

1. Crie uma aplicação no [Mercado Pago Developers](https://www.mercadopago.com.br/developers/pt).
2. Configure a variável `MERCADOPAGO_ACCESS_TOKEN` no ambiente.
3. Na área de Webhooks, cadastre o endereço:

   ```text
   https://SEU_DOMINIO/api/store/payments/mercadopago/webhook
   ```

4. Habilite os eventos de pagamento e configure a assinatura secreta em `MERCADOPAGO_WEBHOOK_SECRET`.
5. Configure `PUBLIC_BASE_URL` com o endereço HTTPS do domínio.
6. Realize os testes com credenciais de teste antes de habilitar o ambiente de produção.

O backend cria a preferência de pagamento no servidor e direciona o cliente ao Checkout Pro.

A venda e a baixa de estoque somente são realizadas após o recebimento de um webhook com assinatura válida e a consulta do pagamento diretamente à API do Mercado Pago.

O retorno do navegador, isoladamente, não aprova pedidos.

### 3.2 Melhor Envio — cotação de frete

1. Crie ou autorize o aplicativo no Melhor Envio.
2. Gere o token de API.
3. Configure as variáveis:

   - `MELHORENVIO_TOKEN`
   - `STORE_ORIGIN_CEP`
   - `STORE_USER_AGENT`
   - Dimensões e peso padrão do pacote.

4. Inicie os testes com `MELHORENVIO_ENV=sandbox`.
5. Utilize `production` somente após validar a conta e a integração.

O servidor calcula o frete utilizando os dados dos produtos e o CEP informado pelo cliente. A cotação é recalculada no momento da criação do pedido.

O sistema não aceita valores de frete enviados diretamente pelo navegador.

A emissão e a compra de etiquetas, assim como o rastreamento automático, dependem da configuração logística e do fluxo de contratação da conta. O painel administrativo permite registrar manualmente o código de rastreio por meio da API administrativa.

---

## 4. Operação e rotas da aplicação

### Páginas principais

| Rota | Descrição |
|---|---|
| `/` | Loja virtual |
| `/admin` | Painel administrativo protegido por HTTP Basic |
| `/docs` | Documentação interativa da API |
| `/api/health` | Verificação de saúde e configuração da aplicação |

### APIs da loja

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/store/products` | Lista produtos disponíveis |
| GET | `/api/store/products/{id}` | Consulta um produto |
| POST | `/api/store/register` | Cadastro de cliente |
| POST | `/api/store/login` | Autenticação do cliente |
| GET | `/api/store/me` | Consulta a conta autenticada |
| POST | `/api/store/shipping/quote` | Consulta cotação de frete |
| POST | `/api/store/orders` | Criação de pedido |
| GET | `/api/store/orders` | Consulta pedidos autenticados |
| POST | `/api/store/payments/mercadopago/webhook` | Recebimento de webhook validado por HMAC |
| GET | `/api/store/admin/orders` | Consulta pedidos no painel |
| POST | `/api/store/admin/orders/{id}/approve` | Aprovação administrativa |
| POST | `/api/store/admin/orders/{id}/cancel` | Cancelamento administrativo |
| PUT | `/api/store/admin/orders/{id}/tracking` | Registro de código de rastreio |

### Regras operacionais

- Pedidos via Mercado Pago não podem ser aprovados manualmente antes da confirmação do gateway.
- Pedidos com pagamento na entrega dependem da confirmação operacional da loja.
- O estoque é baixado somente na aprovação do pedido, após nova validação de saldo.
- O endpoint de saúde não deve expor segredos ou credenciais.

---

## 5. Segurança

A aplicação possui os seguintes mecanismos:

- Senhas de clientes derivadas com PBKDF2-HMAC-SHA256 e salt aleatório.
- Token de cliente assinado, com expiração de sete dias.
- APIs administrativas protegidas por HTTP Basic.
- APIs públicas sem exposição de custos, lucros ou dados de terceiros.
- Validação de preços, estoque, frete e confirmação de pagamento no servidor.
- Segredos e credenciais configurados por variáveis de ambiente.

Não utilize o servidor de desenvolvimento com `--reload` em produção. Utilize um servidor ASGI atrás de um proxy HTTPS, com backups e monitoramento configurados.

---

## 6. Produção — checklist

Antes de publicar a aplicação, confira:

- [ ] Domínio próprio apontado para a hospedagem.
- [ ] Certificado HTTPS válido.
- [ ] `APP_ENV=production`.
- [ ] `SEED_DEMO_DATA=false`.
- [ ] Todas as variáveis obrigatórias preenchidas.
- [ ] `ADMIN_USERNAME` e `ADMIN_PASSWORD` fortes e exclusivos.
- [ ] `STORE_SECRET` aleatório, com pelo menos 32 caracteres.
- [ ] `PUBLIC_BASE_URL` configurado com HTTPS.
- [ ] Access Token e assinatura de webhook do Mercado Pago configurados no ambiente correto.
- [ ] Token do Melhor Envio e dados reais de origem, peso e dimensões configurados.
- [ ] Produtos, fotos, preços, variações e estoque conferidos.
- [ ] Política de privacidade e termos publicados.
- [ ] Informações sobre trocas, devoluções, prazos, contato e dados fiscais publicadas.
- [ ] Backup automático do SQLite configurado.
- [ ] Monitoramento, logs e política de retenção de dados configurados.
- [ ] Testes de compra realizados com credenciais de teste.
- [ ] Validação final realizada antes da operação em produção.

A aplicação bloqueia a inicialização em modo de produção quando faltam variáveis essenciais.

O ambiente de hospedagem, DNS, certificado TLS e contas externas precisam ser provisionados pelo titular, fora do código.

---

# 7. AT2 — Qualidade e Testes de Software

Esta seção documenta as implementações e os procedimentos de teste desenvolvidos para a atividade avaliativa de Qualidade e Teste de Software (QTS).

A suíte contempla testes de integração, fixtures, mocks, Faker, testes E2E com Playwright, auditoria de acessibilidade com Axe-core e testes de carga com Locust.

## 7.1 Dependências de desenvolvimento

Instale as dependências de desenvolvimento:

```powershell
uv sync --extra dev
```

Instale o navegador Chromium utilizado pelo Playwright:

```powershell
uv run playwright install chromium
```

## 7.2 Testes de integração

Os testes de integração utilizam:

- `TestClient` para testar as rotas da aplicação.
- `@pytest.fixture` para preparar e finalizar recursos de teste.
- `yield` para setup e teardown.
- SQLite temporário para isolamento do banco de dados.
- Factory com `Faker("pt_BR")` para geração de dados sintéticos.
- `pytest-mock` e `mocker.patch` para simular dependências externas.
- Verificação de códigos HTTP e conteúdo dos payloads.

Os testes devem seguir o padrão AAA:

1. **Arrange:** preparação dos dados e ambiente.
2. **Act:** execução da ação que será testada.
3. **Assert:** verificação dos resultados.

Execute os testes de integração:

```powershell
uv run pytest -m integration -v
```

## 7.3 Testes E2E com Playwright

Os testes End-to-End verificam os fluxos da interface web em um navegador real.

A implementação utiliza:

- `pytest-playwright`.
- Page Object Model (POM).
- Seletores semânticos, como `get_by_role`, `get_by_label` e `get_by_text`.
- Verificação de navegação e disponibilidade de elementos da interface.

Para executar os testes, primeiro inicie a aplicação em um terminal:

```powershell
uv run uvicorn app.main:app --reload
```

Mantenha o servidor em execução e abra outro terminal na pasta do projeto.

Execute:

```powershell
uv run pytest -m e2e -v
```

Se a aplicação estiver disponível em outro endereço, configure a variável `E2E_BASE_URL`:

```powershell
$env:E2E_BASE_URL="http://127.0.0.1:8000"
```

## 7.4 Testes de acessibilidade — Axe-core

A auditoria automatizada utiliza `axe-playwright-python` para verificar critérios de acessibilidade baseados nas diretrizes WCAG 2.1 níveis A e AA.

São avaliadas as páginas:

- Página inicial da loja.
- Catálogo de produtos.

Também existe um teste de navegação por teclado que utiliza a tecla `Tab` e verifica o foco dos elementos com `to_be_focused()`.

Com o servidor iniciado, execute:

```powershell
uv run pytest -m accessibility -v
```

Os resultados da auditoria devem ser analisados e eventuais violações corrigidas.

## 7.5 Testes de carga e performance — Locust

O projeto utiliza Locust para simular múltiplos usuários acessando a aplicação simultaneamente.

O arquivo `locustfile.py` define os usuários virtuais por meio de `HttpUser` e as operações simuladas com `@task`.

Com o servidor em execução, abra outro terminal e execute:

```powershell
uv run locust -f locustfile.py --host http://127.0.0.1:8000
```

Acesse a interface web do Locust:

http://localhost:8089

Informe a quantidade de usuários simultâneos e a taxa de inicialização. Inicie o teste e acompanhe os resultados.

### Métricas de desempenho

Após a execução, registre os valores reais apresentados pelo Locust.

| Execução | Usuários | RPS | p95 (ms) | Falhas (%) |
|---|---:|---:|---:|---:|
| A preencher após execução | — | — | — | — |

**Descrição das métricas:**

- **RPS:** quantidade de requisições processadas por segundo.
- **p95:** tempo de resposta abaixo do qual 95% das requisições foram concluídas.
- **Falhas (%):** percentual de requisições que apresentaram erro.

Não utilize valores estimados. Registre somente os resultados obtidos na execução real.

## 7.6 Execução da suíte de testes

Para executar todos os testes:

```powershell
uv run pytest -v
```

Para executar cada categoria separadamente:

```powershell
# Integração
uv run pytest -m integration -v

# E2E
uv run pytest -m e2e -v

# Acessibilidade
uv run pytest -m accessibility -v
```

Os testes E2E e de acessibilidade precisam que a aplicação esteja disponível no endereço configurado em `E2E_BASE_URL`.

Verificação de sintaxe do JavaScript da loja:

```powershell
node --check app/static/store/assets/js/store.js
```

---

## 8. Estrutura do projeto

```text
northmen-store/
├── app/
│   ├── main.py
│   ├── integrations.py
│   └── static/
│       ├── index.html
│       ├── store/
│       └── images/
├── tests/
│   ├── conftest.py
│   ├── test_integration.py
│   ├── e2e/
│   └── accessibility/
├── locustfile.py
├── .env.example
├── .gitignore
├── AGENTS.md
├── AI_USAGE.md
├── PRD.md
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 9. Governança e transparência no uso de IA

A documentação do projeto inclui arquivos específicos para registrar os requisitos, as regras de contexto e a utilização de ferramentas de inteligência artificial:

- `PRD.md`: especificação dos requisitos e funcionalidades do sistema.
- `AGENTS.md`: regras e orientações de contexto para ferramentas de IA.
- `AI_USAGE.md`: transparência sobre ferramentas utilizadas, finalidade do uso e auditoria das alterações.

As alterações realizadas com auxílio de IA devem ser revisadas e validadas antes de sua incorporação ao projeto.

---

## 10. Entrega da AT2

A entrega acadêmica deve conter:

1. **Repositório público no GitHub:** código-fonte, documentação, configuração do projeto, testes e arquivo de carga.
2. **Vídeo demonstrativo individual:** gravação de tela com explicação em áudio, de até quatro minutos.
3. **Demonstração dos testes:** integração, Fixtures, Mocks, Faker, Playwright, POM, Axe-core e Locust.
4. **Resultados de performance:** métricas reais de RPS, p95 e taxa de falhas registradas no README.

O vídeo pode ser hospedado no YouTube como Não Listado, Google Drive, Loom ou plataforma equivalente, desde que o acesso esteja liberado para avaliação.

**Importante:** conferir a visibilidade pública do repositório e a acessibilidade do vídeo antes de realizar a submissão acadêmica.