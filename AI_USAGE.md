# Uso de Inteligência Artificial

A inteligência artificial foi utilizada como apoio ao planejamento, estruturação e implementação inicial do projeto NORTHMEN.

## Atividades apoiadas por IA
- Organização dos requisitos em módulos e regras de negócio.
- Proposta de arquitetura com FastAPI, Pydantic, SQLite e interface HTML.
- Geração de uma primeira versão de endpoints, modelos de validação e estrutura de banco.
- Criação de uma interface administrativa responsiva.
- Elaboração de cenários de testes de integração com Pytest, TestClient, fixtures, Faker e mocks.
- Produção da documentação técnica inicial.

## Revisão humana necessária
O código gerado deve ser revisado e validado pela equipe responsável. Em especial:
- Executar os testes no ambiente local.
- Conferir regras comerciais, cálculos e permissões.
- Substituir dados demonstrativos por dados reais autorizados.
- Implementar autenticação, autorização, backups e controles de segurança antes de uso em produção.

A IA foi utilizada como ferramenta de apoio; decisões finais, validação e responsabilidade pelo projeto permanecem com a pessoa desenvolvedora.

## Expansão da loja virtual
A implementação assistida por IA adicionou uma camada de loja em `app/static/store/`, endpoints de catálogo/autenticação/pedidos em `app/main.py`, aprovação administrativa de pedidos, documentação e testes de integração. As alterações preservam as rotas e tabelas administrativas originais, com migração aditiva do SQLite. O checkout não processa pagamentos: Pix e pagamento na entrega exigem conferência manual. Revisão humana necessária antes de produção, especialmente para credenciais, HTTPS, proteção contra abuso, política de privacidade, regras de frete e integração de pagamentos.


## Integrações comerciais (novembro/2026)
- Foi adicionada uma camada HTTP server-side em `app/integrations.py` para Mercado Pago Checkout Pro e cotação Melhor Envio.
- Nenhuma chave real é armazenada no código; usar `.env.example` como modelo e manter `.env` fora do Git.
- O webhook do Mercado Pago valida `x-signature`/`x-request-id` e confirma o pagamento consultando a API antes de criar venda/baixar estoque.
- O frete é recalculado no servidor a partir do CEP e dados de pacote configuráveis; dimensões e peso precisam ser ajustados ao produto real.
- A integração não substitui validação operacional, cadastro do remetente, compra de etiqueta, emissão fiscal, hospedagem HTTPS ou revisão jurídica das páginas comerciais.
