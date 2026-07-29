# Roadmap

> O que está pronto, o que vem a seguir e - igualmente importante - o que está
> explicitamente **fora de escopo**. Um roadmap que só lista features é marketing;
> este desenha a fronteira do problema.

- [Legenda de status](#legenda-de-status)
- [Marcos](#marcos)
- [Fora de escopo (de propósito)](#fora-de-escopo-de-propósito)
- [Questões em aberto](#questões-em-aberto)

---

## Legenda de status

| Marca | Significado |
|---|---|
| ✅ | Pronto |
| 🚧 | Em progresso |
| ⬜ | Planejado |
| ❄️ | Deliberadamente adiado / precisa de decisão |

## Marcos

### M0 - Design de referência ✅
O sistema totalmente especificado nas docs: regras de domínio, arquitetura,
algoritmos, métricas, observabilidade, estratégia de testes, ADRs e diagramas.

### M1 - Core engine ✅
- ✅ Value objects (`models.py`)
- ✅ Calendar engine (`hebrew.py`, `astronomy.py`, `holidays.py`) + opinion registry
- ✅ `merge_adjacent` + canonicidade de interval, com property tests
- ✅ Golden fixtures para o calendário hebraico + faixas do modelo solar
- ✅ Harness do contrato de determinismo ([TESTING §4](TESTING.md#4-contrato-de-determinismo))

### M2 - Scheduling ✅
- ✅ Shift generator (`daily`, `weekly`)
- ✅ Load model + weights
- ✅ Matriz de feasibility
- ✅ Allocator heurístico (greedy + local search) com objetivo de min-max spread
- ✅ Módulo de metrics (Jain, Gini, spread, equity gap)

### M3 - CLI e exports ✅
- ✅ `schedule`, `explain-boundary`, `fairness`, `validate` ([CLI.md](CLI.md))
- ✅ Writers iCal + JSON
- ✅ Emissão de audit trail + metrics JSON ([OBSERVABILITY.md](OBSERVABILITY.md))
- ✅ Modo `--gate` + exit codes

### M4 - Escala e polimento ⬜
- ⬜ Regime `exact` (ILP via HiGHS) atrás de um extra opcional, com report de gap de
  otimalidade ([ADR-0006](adr/0006-estrategia-de-alocacao.md))
- ⬜ Policy `follow_the_sun`
- ⬜ Logging estruturado (`structlog`) e traces OpenTelemetry
- ⬜ Backup pool para shifts uncoverable

### M5 - Integrações de ecossistema ❄️
- ❄️ Adapters de export PagerDuty / Opsgenie / Grafana OnCall
- ❄️ Wrapper de GitHub Action para o gate de CI

## Fora de escopo (de propósito)

Ser explícito aqui evita scope creep e define expectativas honestas.

| Não faremos | Por quê |
|---|---|
| **Ser um sistema de paging** | Ele produz um schedule; o seu pager existente pagina. Construir um pager é um produto diferente e maior. |
| **Ser uma autoridade haláchica** | Ele calcula *zmanim* de uso comum com opiniões citadas e configuráveis. Não decide *halacha*; o *psak* da comunidade é o input ([ADR-0003](adr/0003-shitah-como-parametro.md)). |
| **Swaps em tempo real / overrides ao vivo** | A ferramenta é batch determinística ([ADR-0005](adr/0005-batch-stateless-vs-servico.md)). Mutação ao vivo é preocupação de serviço; se necessário, um serviço fino envolve o mesmo core. |
| **SaaS hospedado / contas / telemetria** | Offline, local, sem rede ([SECURITY.md](SECURITY.md)). |
| **Observâncias não-judaicas** | O domain model é específico e honesto quanto a isso. A *arquitetura* (um provider plugável de restricted interval) poderia hospedar outros calendários depois, mas é um esforço separado e bem-escopado - não uma promessa vaga de "suportar todas as religiões". |
| **Otimizar para milhões de shifts** | A escala de time é o ponto de design ([ALGORITHMS §7](ALGORITHMS.md#7-complexidade)). Corretude e fairness batem throughput aqui. |

## Questões em aberto

Tracked honestamente em vez de escondidas:

1. **Múltiplos observantes, uma região, Yom Tov longo.** Quando um time inteiro de
   uma única região está restrito simultaneamente, a cobertura genuinamente não pode
   vir de dentro do time. Postura atual: falhar alto + backup pool
   ([ALGORITHMS §6](ALGORITHMS.md#6-tratando-shifts-uncoverable)). Existe um default
   melhor? ❄️
2. **Fairness sub-diária.** Os weights capturam burden de weekend/night, mas não
   *volume de incidentes* (algumas terças são piores que alguns sábados). O load
   model deveria opcionalmente ingerir contagens históricas de page? ⬜
3. **Herança de opinião.** Um time deveria declarar uma *shitah* default que os
   membros herdam salvo override, para reduzir config por membro? Provavelmente sim;
   precisa de uma decisão de schema. ⬜
