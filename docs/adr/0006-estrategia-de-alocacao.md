# ADR-0006: Heurística determinística por padrão, ILP exato opcional em escala

- **Status:** Aceito
- **Data:** 2026-01-10
- **Decisores:** mantenedores

## Contexto

O problema central de scheduling — atribuir cada shift a um membro feasible
minimizando o desbalanceamento de weighted load — é um problema de atribuição com
constraints ([ALGORITHMS §5](../ALGORITHMS.md#5-alocação)). Podemos resolvê-lo
**exatamente** como um integer linear program, ou **aproximadamente** com uma
heurística greedy + local search. O exato dá um resultado de fairness comprovadamente
ótimo mas escala pior; a heurística escala mas abre mão da garantia de otimalidade. O
ponto de design é escala de time (dezenas de pessoas, ~90–180 shifts por window).

## Decisão

Entregar um **allocator heurístico determinístico** como padrão, e manter um ILP exato
como um regime opcional, gated por dependência, para times que querem um ótimo
comprovável:

1. **Heurística (padrão entregue, zero-dependency).** Weighted least-loaded greedy
   (shift mais pesado primeiro, tie-break estável `(-weight, id)`) seguido de local
   search redutor de variância sobre reatribuições feasible. Totalmente
   determinístico; na prática atinge uma alocação parelha e de baixo spread na escala
   de time (o time de exemplo cai em Jain 1.000, spread 1.0). Escolhido como padrão
   porque não precisa de solver de terceiros, o que preserva a garantia zero-dependency
   e offline ([ADR-0002](0002-zmanim-astronomico-vs-lookup-table.md)).
2. **Exato (opcional, `--regime exact`).** Resolve o ILP de min–max spread com um
   solver (ex. HiGHS) para um ótimo comprovável. Mantido atrás de um extra opcional
   para o install core permanecer sem dependências; reservado para casos em que a
   otimalidade precisa ser certificada, não apenas atingida.

Ambas as regimes honram as mesmas constraints hard (feasibility, coverage) e o mesmo
[contrato de determinismo](../TESTING.md#4-contrato-de-determinismo).

## Consequências

**Bom**
- O caso comum recebe um schedule justo e previsível sem nenhuma dependência externa.
- O sistema termina rápido e de forma previsível mesmo em times incomumente grandes.
- Honestidade: quando o exato é usado, sua garantia é explícita; a heurística nunca
  finge ser ótima.
- Uma única função objetivo orienta ambas as regimes, então o comportamento é
  consistente.

**Ruim / custo**
- Dois caminhos de código para manter e testar. Mitigado por compartilhar o objetivo,
  as constraints e o formato de audit; ambos são cobertos pela suíte property
  (fairness ≥ baseline round-robin vale para os dois).
- O ILP adiciona uma dependência de solver — por isso fica atrás de um extra opcional,
  fora do install padrão.

## Alternativas consideradas

- **Só exato por padrão:** garantia mais limpa, mas adiciona um solver ao install core
  e pode travar num input patologicamente grande sem escape hatch. Rejeitado como
  padrão em favor de degradação graciosa e zero-dependency.
- **Constraint-programming (CP-SAT) em vez de ILP:** viável e possivelmente mais rápido
  em algumas instâncias; mantido como troca futura atrás da mesma interface de
  objetivo. Não necessário na escala atual.
