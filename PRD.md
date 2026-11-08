# PRD — ARENA WEAR
## Sistema de Gestão e Loja Virtual

**Projeto:** ARENA WEAR  
**Segmento:** Streetwear e moda urbana  
**Tipo de aplicação:** Sistema web de gestão comercial e comércio eletrônico  
**Tecnologias principais:** Python, FastAPI, Pydantic, SQLite, HTML, CSS e JavaScript  
**Gerenciamento de dependências:** uv  
**Atividade:** AT2 — Testes de Integração, E2E, Acessibilidade e Qualidade Não Funcional (QTS)

---

# 1. Visão geral do produto

A ARENA WEAR é uma aplicação web desenvolvida para auxiliar a gestão e a operação de uma loja de streetwear e moda urbana.

O sistema reúne duas áreas integradas em uma única aplicação:

- **Painel administrativo:** destinado ao gerenciamento de produtos, estoque, clientes, vendas e indicadores comerciais.
- **Loja virtual:** destinada à apresentação dos produtos, navegação pelo catálogo, cadastro de clientes, realização de pedidos e acompanhamento de compras.

As duas áreas compartilham a mesma aplicação desenvolvida com FastAPI e a mesma base de dados SQLite, mantendo a integração entre as operações administrativas e as atividades realizadas pelos clientes.

O projeto também contempla integrações externas para cotação de frete e processamento de pagamentos, além de uma estrutura de testes automatizados voltada à avaliação da qualidade do software.

# 2. Objetivos do produto

## 2.1 Objetivo geral

Desenvolver uma plataforma integrada que facilite o gerenciamento das atividades comerciais da ARENA WEAR e disponibilize uma experiência de compra digital aos clientes.

## 2.2 Objetivos específicos

- Centralizar o cadastro e o gerenciamento de produtos.
- Controlar o estoque por produto, tamanho e cor.
- Registrar vendas e acompanhar o histórico de movimentações.
- Gerenciar clientes e informações de compras.
- Apresentar indicadores de faturamento, vendas e lucro bruto estimado.
- Disponibilizar um catálogo virtual com pesquisa e filtros.
- Permitir cadastro, autenticação e consulta de pedidos pelos clientes.
- Implementar um processo de checkout com validação de estoque e cálculo de frete.
- Integrar pagamentos online por meio do Mercado Pago.
- Avaliar a qualidade do sistema utilizando testes de integração, testes E2E, auditoria de acessibilidade e testes de carga.

# 3. Público-alvo

O sistema possui dois grupos principais de usuários:

**3.1 Administradores e equipe da loja**

Proprietário e colaboradores responsáveis pelo atendimento, gerenciamento de produtos, controle de estoque, registro de vendas e acompanhamento dos resultados comerciais.

**3.2 Clientes**

Pessoas interessadas em adquirir produtos de streetwear e moda urbana, que utilizam a loja virtual para consultar o catálogo, selecionar variações, realizar pedidos e acompanhar suas compras.

# 4. Escopo do sistema

## 4.1 Painel administrativo

O painel administrativo é destinado à gestão interna da ARENA WEAR e permanece integrado à aplicação principal.

**Dashboard**

Apresenta informações resumidas sobre a operação da loja, incluindo:

- Faturamento mensal.
- Quantidade de vendas realizadas no dia.
- Estimativa de lucro bruto.
- Total de produtos ativos.
- Alertas de estoque baixo.
- Histórico de vendas recentes.

**Gerenciamento de produtos**

Permite cadastrar, consultar, pesquisar, editar e arquivar produtos, armazenando informações como nome, categoria, descrição, preço de venda, custo, imagem e variações disponíveis.

**Controle de estoque**

Permite consultar e movimentar o estoque por produto, tamanho e cor, registrando entradas e saídas e impedindo operações que resultem em saldo negativo.

**Gerenciamento de vendas**

Permite registrar vendas, selecionar produtos e respectivas variações, informar cliente, desconto e forma de pagamento, calcular o total e atualizar o estoque após a confirmação da operação.

**Gerenciamento de clientes**

Permite cadastrar e consultar clientes, além de acompanhar a quantidade de compras e o valor total gasto.

**Relatórios**

Apresenta informações para acompanhamento da operação, incluindo unidades vendidas, lucro bruto estimado por produto e variações com estoque reduzido.

## 4.2 Loja virtual

A loja virtual oferece uma interface pública para apresentação e comercialização dos produtos da ARENA WEAR.

**Página inicial**

Apresenta a identidade visual da marca, banners promocionais, destaques e acesso às principais áreas da loja.

**Catálogo de produtos**

Permite consultar os produtos disponíveis, pesquisar por nome e aplicar filtros por categoria.

**Detalhes do produto**

Apresenta imagens, descrição, preço e opções de tamanho e cor, além da disponibilidade de estoque por variação.

**Carrinho de compras**

Permite adicionar produtos, alterar quantidades, remover itens e consultar o subtotal da compra.

**Cadastro e autenticação**

Permite que clientes criem uma conta, realizem login e acessem uma área pessoal protegida por sessão autenticada.

**Área do cliente**

Disponibiliza informações da conta e histórico de pedidos associados ao cliente autenticado.

**Checkout**

Permite informar endereço de entrega, CEP, consultar opções de frete e selecionar a modalidade de pagamento disponível.

**Acompanhamento de pedidos**

Permite consultar pedidos e informações de rastreamento disponibilizadas pela loja.

# 5. Requisitos funcionais

Os requisitos funcionais descrevem as operações que o sistema deve disponibilizar aos seus usuários.

| Código | Módulo | Requisito funcional |
|---|---|---|
| RF01 | Dashboard | Exibir indicadores comerciais e vendas recentes. |
| RF02 | Produtos | Cadastrar produtos com informações comerciais. |
| RF03 | Produtos | Consultar, pesquisar e listar produtos. |
| RF04 | Produtos | Editar e arquivar produtos. |
| RF05 | Estoque | Consultar estoque por tamanho e cor. |
| RF06 | Estoque | Registrar entradas e saídas de produtos. |
| RF07 | Estoque | Impedir movimentações que gerem saldo negativo. |
| RF08 | Vendas | Registrar vendas com itens, descontos e pagamento. |
| RF09 | Vendas | Calcular o total e atualizar o estoque após a venda. |
| RF10 | Clientes | Cadastrar e consultar clientes. |
| RF11 | Relatórios | Apresentar informações de vendas, lucro e estoque crítico. |
| RF12 | Catálogo | Exibir produtos disponíveis na loja virtual. |
| RF13 | Pesquisa | Permitir pesquisa e filtragem de produtos. |
| RF14 | Carrinho | Adicionar, alterar e remover produtos do carrinho. |
| RF15 | Cadastro | Permitir cadastro e autenticação de clientes. |
| RF16 | Conta | Disponibilizar informações pessoais e histórico de pedidos. |
| RF17 | Frete | Consultar opções e valores de entrega pelo Melhor Envio. |
| RF18 | Pedidos | Criar pedidos com validação de dados e estoque no servidor. |
| RF19 | Pagamento | Criar preferências de pagamento pelo Mercado Pago. |
| RF20 | Pagamento | Validar notificações de pagamento e consultar o gateway. |
| RF21 | Pedidos | Permitir aprovação e cancelamento administrativo conforme as regras de pagamento. |
| RF22 | Rastreamento | Registrar código de rastreio dos pedidos. |
| RF23 | Saúde | Disponibilizar endpoint para verificação da aplicação. |

# 6. Regras de negócio

As regras de negócio determinam as condições que devem ser respeitadas durante as operações do sistema.

**RN01 — Preço:** o preço de venda de um produto deve ser maior que zero.

**RN02 — Custo:** o custo cadastrado não pode apresentar valor negativo.

**RN03 — Quantidade:** quantidades movimentadas ou vendidas devem ser números inteiros positivos.

**RN04 — Integridade do estoque:** o sistema não deve permitir que o estoque de uma variação fique negativo.

**RN05 — Desconto:** o desconto aplicado a uma venda não pode ser superior ao subtotal dos itens.

**RN06 — Atualização do estoque:** as operações de venda devem atualizar o estoque correspondente às variações comercializadas.

**RN07 — Arquivamento:** produtos excluídos da operação comercial devem ser arquivados, preservando o histórico de movimentações e vendas.

**RN08 — Cliente de balcão:** uma venda administrativa pode ser registrada com um cliente cadastrado ou como cliente de balcão.

**RN09 — Lucro bruto:** o lucro apresentado nos relatórios é uma estimativa calculada pela diferença entre preço de venda e custo cadastrado, multiplicada pelas unidades vendidas. Não representa lucro líquido e não considera despesas operacionais, impostos ou taxas de pagamento.

**RN10 — Validação do pedido:** preços, quantidades, descontos e valores de frete devem ser recalculados ou validados no servidor, não sendo aceitos como confiáveis quando enviados diretamente pelo navegador.

**RN11 — Pagamento online:** pedidos pagos pelo Mercado Pago somente podem ser aprovados após validação da assinatura do webhook e consulta do pagamento diretamente ao gateway.

**RN12 — Retorno do pagamento:** o redirecionamento do cliente após o checkout não representa confirmação de pagamento.

**RN13 — Pagamento na entrega:** pedidos nessa modalidade dependem de confirmação operacional e aprovação administrativa.

**RN14 — Baixa de estoque do pedido:** a aprovação do pedido deve validar novamente a disponibilidade de estoque antes da baixa.

**RN15 — Dados do cliente:** clientes autenticados podem consultar somente os próprios dados e pedidos.

# 7. Rotas e interfaces do sistema

## 7.1 Páginas web

| Endereço | Descrição |
|---|---|
| `/` | Página inicial da loja virtual. |
| `/admin` | Painel administrativo protegido por HTTP Basic. |
| `/products.html` | Catálogo de produtos. |
| `/docs` | Documentação interativa da API. |

As páginas públicas da loja estão organizadas em `app/static/store/`, enquanto o painel administrativo permanece em `app/static/index.html`.

## 7.2 Rotas da API administrativa

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/health` | Verifica a saúde da aplicação. |
| GET | `/api/dashboard` | Consulta indicadores do painel. |
| GET / POST | `/api/products` | Lista, pesquisa e cadastra produtos. |
| PUT / DELETE | `/api/products/{id}` | Atualiza ou arquiva produtos. |
| GET | `/api/stock` | Consulta o estoque. |
| POST | `/api/stock/movements` | Registra movimentações de estoque. |
| GET / POST | `/api/customers` | Lista, pesquisa e cadastra clientes. |
| GET / POST | `/api/sales` | Consulta e registra vendas. |
| GET | `/api/reports` | Consulta relatórios comerciais. |

## 7.3 Rotas da loja virtual

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/store/products` | Lista produtos disponíveis para compra. |
| GET | `/api/store/products/{id}` | Consulta os detalhes de um produto. |
| POST | `/api/store/register` | Realiza cadastro de cliente. |
| POST | `/api/store/login` | Autentica o cliente. |
| GET | `/api/store/me` | Consulta os dados da conta autenticada. |
| POST | `/api/store/shipping/quote` | Solicita cotação de frete. |
| POST | `/api/store/orders` | Cria um pedido. |
| GET | `/api/store/orders` | Lista pedidos do cliente autenticado. |
| POST | `/api/store/payments/mercadopago/webhook` | Recebe notificações de pagamento e valida sua assinatura. |

## 7.4 Rotas administrativas da loja

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/store/admin/orders` | Consulta pedidos para gestão administrativa. |
| POST | `/api/store/admin/orders/{id}/approve` | Aprova pedidos conforme as regras de pagamento. |
| POST | `/api/store/admin/orders/{id}/cancel` | Cancela pedidos. |
| PUT | `/api/store/admin/orders/{id}/tracking` | Registra código de rastreamento. |

As rotas administrativas devem exigir autenticação e autorização conforme as configurações do backend.

# 8. Requisitos não funcionais e qualidade de software

Os requisitos não funcionais definem características de qualidade que devem ser avaliadas na aplicação. A especificação considera características da ISO/IEC 25010.

## 8.1 Adequação funcional

O sistema deve disponibilizar funcionalidades compatíveis com os objetivos da loja, executando corretamente operações de cadastro, vendas, estoque, pedidos e relatórios.

**Avaliação:** testes de integração com Pytest e TestClient, verificando códigos HTTP, respostas e regras de negócio.

## 8.2 Confiabilidade

As operações que envolvem pedidos, vendas e estoque devem preservar a consistência dos dados, evitando baixas duplicadas, registros inconsistentes e saldos negativos.

**Avaliação:** testes de cenários de sucesso e falha, isolamento do banco de dados e validação das operações.

## 8.3 Desempenho e eficiência

A aplicação deve responder adequadamente às requisições e permitir a avaliação do comportamento sob acessos concorrentes.

**Avaliação:** testes de carga com Locust, registrando requisições por segundo (RPS), percentil 95 do tempo de resposta (p95) e percentual de falhas.

## 8.4 Segurança

O sistema deve proteger informações pessoais, credenciais e operações administrativas.

São considerados:
- Hash de senhas com PBKDF2-HMAC-SHA256 e salt aleatório.
- Tokens de autenticação assinados e com expiração.
- Proteção das rotas administrativas.
- Validação dos dados recebidos pela API.
- Proteção dos pagamentos por validação de assinatura de webhook.
- Armazenamento de segredos em variáveis de ambiente.
- Não exposição de custos, lucros e dados privados nas APIs públicas.

**Avaliação:** testes de autenticação, autorização, validação de dados e cenários de falha.

## 8.5 Usabilidade

A interface deve apresentar navegação intuitiva, informações organizadas e mensagens compreensíveis, facilitando a utilização por administradores e clientes.

**Avaliação:** testes E2E com Playwright, verificando os principais fluxos e elementos das interfaces.

## 8.6 Acessibilidade

As páginas avaliadas devem seguir boas práticas de acessibilidade, considerando as diretrizes WCAG 2.1 níveis A e AA.

São avaliados:
- Identificação acessível de elementos interativos.
- Uso adequado de títulos e elementos semânticos.
- Identificação de campos de formulário.
- Contraste e legibilidade.
- Navegação por teclado.
- Visibilidade e ordem do foco.

**Avaliação:** auditoria automatizada com Axe-core e testes de navegação utilizando a tecla Tab e verificações de foco com Playwright.

## 8.7 Manutenibilidade

O código deve possuir organização que facilite sua compreensão, manutenção e evolução.

São consideradas:
- Separação de responsabilidades.
- Organização dos arquivos e módulos.
- Documentação técnica.
- Testes automatizados.
- Gerenciamento de dependências com uv.
- Registro das decisões e alterações apoiadas por ferramentas de IA.

**Avaliação:** revisão da estrutura do projeto, documentação e execução da suíte de testes.

## 8.8 Compatibilidade

A interface deve funcionar em navegadores modernos compatíveis com os recursos utilizados e apresentar comportamento responsivo em diferentes tamanhos de tela.

**Avaliação:** execução de testes E2E nos navegadores e ambientes suportados pelo projeto.

# 9. Estratégia de testes e validação

A qualidade da aplicação será avaliada por diferentes níveis de teste, conforme os requisitos da AT2.

## 9.1 Testes de integração

Utilizam Pytest e FastAPI TestClient para verificar a comunicação entre rotas, regras de negócio e persistência de dados.

A implementação contempla:
- Marcador `@pytest.mark.integration`.
- Fixtures com `@pytest.fixture` e `yield`.
- Banco SQLite temporário para isolamento.
- Massa de dados com `Faker("pt_BR")`.
- Factory para geração de dados sintéticos.
- Mocks com `pytest-mock` e `mocker.patch`.
- Verificação de status HTTP e conteúdo dos payloads.
- Organização dos testes pelo padrão Arrange, Act e Assert (AAA).

## 9.2 Testes End-to-End

Utilizam Playwright para simular a interação de usuários com a interface web.

A implementação contempla:
- Marcador `@pytest.mark.e2e`.
- Page Object Model (POM).
- Seletores semânticos, como `get_by_role`, `get_by_label` e `get_by_text`.
- Verificação de carregamento e navegação.
- Validação de elementos e funcionalidades da interface.

## 9.3 Testes de acessibilidade

Utilizam Axe-core para auditoria automatizada dos critérios WCAG 2.1 níveis A e AA.

Também são realizados testes de navegação por teclado, verificando a movimentação do foco com Tab e a identificação dos elementos focados.

## 9.4 Testes de carga

Utilizam Locust para simular usuários concorrentes acessando endpoints da aplicação.

As métricas observadas são:
- **RPS:** requisições processadas por segundo.
- **p95:** percentil 95 do tempo de resposta.
- **Taxa de falhas:** percentual de requisições que apresentaram erro.

Os resultados devem ser registrados no README após a execução real dos testes, sem utilização de valores estimados.

# 10. Tecnologias e ferramentas

| Tecnologia | Finalidade |
|---|---|
| Python 3.12+ | Linguagem principal. |
| FastAPI | Desenvolvimento da API e aplicação web. |
| Pydantic | Validação e estruturação de dados. |
| SQLite | Persistência dos dados. |
| HTML5 | Estrutura das interfaces. |
| CSS3 | Estilização e responsividade. |
| JavaScript | Interatividade da loja virtual. |
| uv | Gerenciamento de dependências e execução. |
| Pytest | Execução dos testes automatizados. |
| FastAPI TestClient | Testes das rotas da aplicação. |
| pytest-mock | Simulação de dependências externas. |
| Faker | Geração de dados sintéticos. |
| Playwright | Testes E2E e interação com navegador. |
| Page Object Model | Organização dos testes de interface. |
| Axe-core | Auditoria automatizada de acessibilidade. |
| Locust | Testes de carga e desempenho. |
| Git e GitHub | Controle de versão e publicação do projeto. |

# 11. Integrações externas

## 11.1 Mercado Pago

Responsável pelo processamento de pagamentos online por meio do Checkout Pro, com suporte às modalidades disponibilizadas pela conta de integração.

O backend cria as preferências de pagamento e recebe notificações por webhook. A confirmação do pagamento depende da validação da assinatura e da consulta direta ao gateway.

As credenciais devem ser configuradas por variáveis de ambiente, utilizando credenciais de teste durante a validação.

## 11.2 Melhor Envio

Responsável pela cotação de frete com base no CEP de destino e nas informações dos produtos.

O backend consulta a integração externa e valida a modalidade de entrega no momento da criação do pedido.

A compra de etiquetas e o rastreamento automático dependem das funcionalidades e configurações logísticas disponíveis na conta.

# 12. Fora do escopo e limitações

A primeira versão do sistema de gestão não contemplava integrações com marketplaces, emissão fiscal, leitura de código de barras, gateway de pagamento real, autenticação multiusuário, armazenamento de imagens em nuvem ou sincronização entre filiais.

Na expansão da ARENA WEAR, foram incorporados recursos de comércio eletrônico e integrações com Mercado Pago e Melhor Envio.

Permanecem dependentes de serviços e configurações externas:
- Hospedagem e domínio público.
- Certificado HTTPS.
- Contas e credenciais dos serviços externos.
- Emissão fiscal.
- Compra de etiquetas de envio.
- Automação logística adicional.
- Políticas comerciais, privacidade e dados fiscais da loja.

# 13. Critérios de aceite

O sistema será considerado funcionalmente validado quando atender aos seguintes critérios:

## 13.1 Gestão administrativa

- [ ] Permitir cadastrar, consultar, editar e arquivar produtos.
- [ ] Permitir registrar entradas e saídas de estoque.
- [ ] Impedir saldo negativo.
- [ ] Registrar vendas com cálculo correto do total.
- [ ] Recusar vendas com estoque insuficiente.
- [ ] Validar descontos e formas de pagamento.
- [ ] Atualizar os indicadores e relatórios com os dados persistidos.

## 13.2 Loja virtual

- [ ] Exibir catálogo e detalhes dos produtos.
- [ ] Permitir pesquisa e filtragem por categoria.
- [ ] Exibir variações de tamanho e cor.
- [ ] Permitir adicionar, atualizar e remover itens do carrinho.
- [ ] Permitir cadastro e autenticação de clientes.
- [ ] Restringir o histórico de pedidos ao cliente autenticado.
- [ ] Calcular o frete no servidor.
- [ ] Criar pedidos com validação de estoque e valores.
- [ ] Validar pagamentos online conforme as regras do Mercado Pago.
- [ ] Permitir operações administrativas de aprovação, cancelamento e rastreamento.

## 13.3 Qualidade e testes

- [ ] Executar os testes de integração com os marcadores e ferramentas exigidos.
- [ ] Validar Fixtures, Mocks, Faker e padrão AAA.
- [ ] Executar os testes E2E com Playwright e POM.
- [ ] Executar a auditoria de acessibilidade com Axe-core.
- [ ] Validar navegação por teclado.
- [ ] Executar o teste de carga com Locust.
- [ ] Registrar as métricas reais de desempenho no README.
- [ ] Executar a suíte completa com `uv run pytest -v`.

## 13.4 Entrega acadêmica

- [ ] Disponibilizar o repositório público no GitHub.
- [ ] Incluir código-fonte, documentação, configuração e testes.
- [ ] Incluir PRD, regras de contexto e relatório de uso de IA.
- [ ] Incluir o README com instruções de instalação e execução.
- [ ] Incluir o arquivo `locustfile.py`.
- [ ] Gravar vídeo individual de até quatro minutos, com áudio e gravação de tela.
- [ ] Apresentar os testes e métricas no vídeo.
- [ ] Disponibilizar o link do vídeo com acesso liberado para avaliação.

# 14. Documentação e governança

O projeto mantém documentação para especificar o funcionamento do sistema, orientar ferramentas de desenvolvimento e registrar o uso de inteligência artificial.

| Arquivo | Finalidade |
|---|---|
| `README.md` | Instruções de instalação, configuração, execução e testes. |
| `PRD.md` | Requisitos, escopo, regras de negócio e critérios de aceite. |
| `AGENTS.md` | Regras e orientações de contexto para ferramentas de IA. |
| `AI_USAGE.md` | Registro das ferramentas de IA utilizadas, finalidades, alterações e auditoria. |
| `pyproject.toml` | Configuração do projeto e dependências. |
| `locustfile.py` | Cenários de simulação de carga. |

As alterações apoiadas por ferramentas de inteligência artificial devem ser revisadas, compreendidas e validadas antes de serem incorporadas ao projeto.

---

**Documento:** PRD — ARENA WEAR  
**Finalidade:** Especificação do produto e referência para desenvolvimento e validação da aplicação na atividade AT2 de QTS.