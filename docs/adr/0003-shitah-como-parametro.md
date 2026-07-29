# ADR-0003: Tratar a opinião haláchica (shitah) como parâmetro

- **Status:** Aceito
- **Data:** 2026-01-07
- **Decisores:** mantenedores

## Contexto

A definição de *tzais* (nightfall) — e, em menor grau, o candle-lighting buffer —
varia entre autoridades haláchicas (*poskim*). Um depression angle de 8.5°, 16.1°, ou
um fixo de 40/72 minutos são todos válidos dependendo do *psak* que uma comunidade
segue ([DOMAIN §5](../DOMAIN.md#5-opiniões-de-zmanim-shitot)). Uma ferramenta que
hard-coda uma opinião está silenciosamente impondo uma decisão religiosa aos seus
usuários, e estará simplesmente *errada* para quem segue outra.

## Decisão

A *shitah* é um **parâmetro de primeira classe**, selecionado por membro. Todas as
opiniões vivem num único **opinion registry** (`calendar/zmanim_opinions.py`), cada
entrada carregando seus parâmetros de cálculo **e uma citação**. Nenhum módulo fora do
registry faz branch por string de *shitah*; o código downstream recebe um objeto de
cálculo já resolvido.

A ferramenta traz defaults sensatos (buffer 18 min, nightfall `gra_8.5`) mas os trata
estritamente como defaults, documentados como tal.

## Consequências

**Bom**
- A ferramenta nunca impõe um *psak*; a decisão da comunidade é o input. É o único
  design honesto para um domínio de observância religiosa.
- Adicionar uma opinião é uma entrada de registry com citação — sem mudança de lógica,
  sem risco ao allocator.
- Boundaries permanecem auditáveis: a opinião escolhida faz parte de todo rationale.
- A monotonicidade de *tzais* entre opiniões é [property-tested](../TESTING.md#3-property-based-tests).

**Ruim / custo**
- Mais superfície de configuração; um time precisa conhecer sua *shitah* (mitigado por
  defaults e, no [roadmap](../ROADMAP.md#questões-em-aberto), herança a nível de time).
- O registry precisa ser curado com cuidado — uma citação errada é um bug de domínio.

## Alternativas consideradas

- **Default único opinativo, sem config:** o mais simples, mas errado para boa parte
  dos usuários e impõe silenciosamente uma decisão. Rejeitado por princípio.
- **Somente inputs livres de ângulo/minutos por membro:** flexível mas perde as
  citações e as opiniões nomeadas e revisáveis. Mantido como escape hatch (`fixed_N`),
  mas as opiniões nomeadas são a interface primária.
