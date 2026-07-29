# ADR-0004: UTC internamente, localizar só nas bordas

- **Status:** Aceito
- **Data:** 2026-01-08
- **Decisores:** mantenedores

## Contexto

O sistema abrange membros em fusos diferentes, calcula eventos solares atrelados ao
tempo solar local, e precisa sobreviver a transições de DST que podem ocorrer
*dentro* de um restricted interval
([DOMAIN edge cases 6–7](../DOMAIN.md#7-edge-cases-que-o-modelo-precisa-sobreviver)).
Misturar tempo de relógio local pelo core é o caminho clássico para bugs de errar por
uma hora e para saída não-reproduzível entre máquinas com locales diferentes.

## Decisão

- **Todos os instants internos são UTC timezone-aware.** Todo restricted interval,
  boundary de shift e comparação acontece em UTC.
- **Hora local existe só nas duas bordas:** parsing de input (a location do membro
  fornece o tz IANA usado para calcular o instant UTC correto) e renderização de
  saída (`explain-boundary`, `TZID` do iCal, relatórios mostram hora local para
  humanos).
- O core lê o tempo exclusivamente por um **`Clock` injetado**; nunca chama
  `datetime.now()` nem lê o timezone ambiente.

## Consequências

**Bom**
- Transições de DST dentro de um interval são um não-evento: UTC é monotônico, então a
  matemática do interval não é afetada; só a *exibição* localizada reflete o salto.
- Times cross-timezone são tratados naturalmente — o interval de cada membro é
  calculado na sua location e comparado num frame comum.
- Sustenta o [contrato de determinismo](../TESTING.md#4-contrato-de-determinismo): sem
  vazamento de locale de máquina ou relógio ambiente no resultado.

**Ruim / custo**
- Exige disciplina: qualquer código novo que toca tempo deve passar pelo `Clock` e
  manter UTC internamente. Forçado em review e pelos testes de determinismo (que rodam
  com clock congelado e exporiam um `now()` perdido).
- A saída voltada a humanos exige um passo explícito de localização; uma localização
  esquecida mostra UTC ao usuário (um bug visível e inofensivo — muito melhor que um
  boundary com hora errada em silêncio).

## Alternativas consideradas

- **Hora local por toda parte:** intuitivo para times de um só fuso, catastrófico para
  multi-fuso e DST. Rejeitado.
- **Datetimes naive (sem tz):** convida à comparação errada silenciosa. Rejeitado;
  somente UTC tz-aware.
