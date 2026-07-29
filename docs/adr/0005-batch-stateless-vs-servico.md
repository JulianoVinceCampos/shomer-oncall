# ADR-0005: Ferramenta batch stateless, não um serviço de longa duração

- **Status:** Aceito
- **Data:** 2026-01-09
- **Decisores:** mantenedores

## Contexto

Um scheduler de plantão poderia ser construído como um serviço persistente (banco de
membros e shifts, uma API, overrides ao vivo, webhooks) ou como uma computação batch
stateless (inputs entram, schedule sai). O modelo de serviço é o que as plataformas
comerciais de paging são. A pergunta é o que *esta* ferramenta deve ser, dados os seus
objetivos: corretude, determinismo, auditabilidade e ser CI-friendly.

## Decisão

Construir uma **CLI batch stateless**. Os inputs são arquivos (team JSON, history +
config opcionais); as saídas são arquivos (schedule, audit trail, metrics) e um exit
code. Sem banco, sem servidor, sem rede em runtime, sem estado persistente
([ARCHITECTURE §1](../ARCHITECTURE.md#1-visão-geral)).

O estado que *é* necessário entre windows (carry-in de fairness) é passado
explicitamente como um arquivo de input ([carry-in de histórico](../ALGORITHMS.md#carry-in-de-histórico)),
não mantido internamente.

## Consequências

**Bom**
- **Determinismo é alcançável** - uma função pura dos seus inputs, sem estado de
  servidor escondido para perturbar a saída.
- **Trivialmente testável** - sem fixtures de DB, sem harness de serviço; a ferramenta
  inteira é `run(inputs) -> outputs`.
- **Nativa de CI** - encaixa num pipeline como gate com [exit codes](../CLI.md#exit-codes)
  significativos; um PR de roster pode ser checado por fairness antes do merge.
- **Superfície de ataque mínima** - nada para autenticar, nada escutando
  ([SECURITY](../SECURITY.md#1-threat-model)).
- **Auditável** - todo run emite um audit trail autocontido.

**Ruim / custo**
- Sem overrides ao vivo ou swaps em tempo real. Um "estou doente, me troca" no mesmo
  dia é tratado re-rodando com um input atualizado, não mutando um schedule ao vivo.
- Fairness cross-window exige que o caller passe o arquivo de history.
- Sem UI embutida; a visualização depende do stack existente do operador
  ([OBSERVABILITY §7](../OBSERVABILITY.md#7-dashboards-e-superfície-em-ci)).

## Reversibilidade

Esta decisão é **barata de revisitar**: como toda a lógica vive no core puro, um
serviço futuro seria um shell fino em volta das mesmas funções - o core não mudaria.
Essa assimetria (batch agora, serviço depois se justificado) é por que batch é o ponto
de partida certo. A demanda por swap ao vivo está tracked no
[roadmap](../ROADMAP.md#fora-de-escopo-de-propósito) como explicitamente fora de
escopo por ora.
