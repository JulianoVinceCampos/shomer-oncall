# ADR-0001: Registrar decisões de arquitetura

- **Status:** Aceito
- **Data:** 2026-01-05
- **Decisores:** mantenedores

## Contexto

`shomer-oncall` faz várias escolhas não-óbvias (cálculo astronômico em vez de lookup
table, opinião-como-parâmetro, batch em vez de serviço). Daqui a seis meses, o
*porquê* de cada uma terá sido esquecido, e alguém vai "consertar" uma decisão
deliberada de volta para um bug. Precisamos de um registro leve e durável das
decisões e do seu rationale, que viva junto do código.

## Decisão

Usamos **Architecture Decision Records** (formato de Michael Nygard) guardados em
`docs/adr/`, numerados sequencialmente, imutáveis uma vez aceitos. Uma decisão é
alterada adicionando um novo ADR que substitui o antigo - nunca editando o histórico.

Cada ADR declara: contexto, a decisão e as consequências (boas e ruins). Uma decisão
por arquivo. Escolhas de design não-triviais em PRs devem chegar com um ADR
([CONTRIBUTING](../../CONTRIBUTING.md#regras-básicas)).

## Consequências

**Bom**
- O rationale fica preservado ao lado do código e é revisado como código.
- Substituir-em-vez-de-editar mantém um histórico honesto de como o pensamento
  evoluiu.
- Novos contribuidores leem o conjunto de ADRs e entendem o formato do sistema rápido.

**Ruim / custo**
- Pequeno overhead por decisão significativa.
- Exige disciplina para os ADRs e as docs narrativas (ARCHITECTURE, DOMAIN) não
  divergirem. Mitigação: as docs narrativas linkam para o ADR pelo *porquê* e nunca
  reafirmam o rationale.
