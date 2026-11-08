# AGENTS.md — Orientações para agentes de IA

## Contexto
Este repositório contém o NORTHMEN, sistema de gestão para uma loja de moda masculina. Backend em Python/FastAPI, validação Pydantic, persistência SQLite e interface HTML/CSS/JavaScript.

## Regras obrigatórias
1. Leia `PRD.md` antes de alterar funcionalidades ou contratos da API.
2. Use Python 3.12 ou superior e gerencie dependências/comandos com `uv`.
3. Mantenha validações de entrada em modelos Pydantic.
4. Não permita estoque negativo; vendas devem baixar estoque de forma consistente.
5. Não remova nem renomeie rotas sem atualizar documentação e testes.
6. Preserve a responsividade e a acessibilidade da interface.
7. Não adicione credenciais, tokens ou dados pessoais reais ao repositório.
8. Prefira alterações pequenas e compatíveis com o código existente.
9. Ao criar ou alterar endpoints, adicione/atualize testes de integração.
10. Não afirme que testes passaram sem executá-los.

## Fluxo recomendado
- Inspecionar código e documentação.
- Implementar a menor alteração que atende ao requisito.
- Executar `uv run pytest`.
- Revisar respostas de erro, validações e efeitos no estoque.
- Atualizar `README.md` e `PRD.md` quando houver mudança de comportamento.

## Convenções
- Nomes de variáveis e funções em `snake_case`.
- Classes Pydantic em `PascalCase`.
- Rotas sob `/api`.
- Valores monetários em reais (BRL), armazenados como números decimais no escopo do protótipo.
- Mensagens e interface em português do Brasil.

## Loja virtual NORTHMEN
- A loja pública vive em `app/static/store/`; não substituir `app/static/index.html`, que é o painel administrativo existente.
- `/` entrega a loja e `/admin` entrega o painel, protegido por HTTP Basic.
- APIs públicas da loja devem usar exclusivamente `/api/store/*` e nunca retornar `cost`, margem, relatórios ou dados de outros clientes.
- APIs de gestão existentes continuam administrativas. Ao acrescentar uma rota, revisar a regra de autenticação do middleware em `app/main.py`.
- Preços, status ativo e estoque devem ser sempre consultados no SQLite pelo backend; não confiar nos valores do carrinho enviados pelo navegador.
- Pedidos começam pendentes. Pagamentos Mercado Pago só aprovam via webhook HMAC validado e consulta server-to-server; pagamento na entrega exige ação administrativa.
- Cotação Melhor Envio deve ser refeita no servidor ao criar pedido; nunca confiar no preço de frete vindo do browser.
- Segredos ficam em `.env`/ambiente; nunca commitar credenciais reais. `.env.example` contém placeholders.
- Em produção, `APP_ENV=production`, HTTPS e todas as integrações obrigatórias devem estar configurados antes do start.
- Não marcar uma loja como pronta para produção até validar domínio, contas externas, política de privacidade/trocas, frete, pagamentos e backup.
- Rodar `uv run pytest` e `node --check app/static/store/assets/js/store.js` após alterações.
