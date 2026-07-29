# Referência da CLI

> `shomer-oncall` é um único comando com subcomandos. Tudo é flag; não há modo
> interativo (mantém tudo scriptável e determinístico). Comportamento global: lê
> arquivos, escreve arquivos, define um exit code. Nunca muta sistemas externos.

- [Subcomando `schedule`](#schedule)
- [Subcomando `explain-boundary`](#explain-boundary)
- [Subcomando `fairness`](#fairness)
- [Subcomando `validate`](#validate)
- [Sintaxe de location](#sintaxe-de-location)
- [Exit codes](#exit-codes)
- [Arquivo de config](#arquivo-de-config)

---

## schedule

Gera uma rotação e escreve a saída.

```bash
shomer-oncall schedule \
  --team ./examples/team.json \
  --from 2026-01-01 --to 2026-03-31 \
  --config ./examples/shomer.toml \
  --out out/schedule.ics \
  --format ics,json \
  --history ./prev-loads.json \
  --gate
```

| Flag | Default | Significado |
|---|---|---|
| `--team PATH` | *(obrigatório)* | Definição de time (JSON; YAML com o extra `yaml`). |
| `--from DATE` / `--to DATE` | *(obrigatório)* | Window inclusiva, ISO `YYYY-MM-DD`. |
| `--out PATH` | `schedule.ics` | Path base de saída (o diretório é criado se faltar). |
| `--format` | `ics,json` | Lista separada por vírgula: `ics`, `json`. Sempre também escreve `*.audit.json` + `*.metrics.json`. |
| `--config PATH` | none | Arquivo TOML/JSON de config. |
| `--history PATH` | none | Loads anteriores para [fairness de rolling-horizon](ALGORITHMS.md#carry-in-de-histórico). |
| `--gate` | off | Força os [thresholds de SLO](METRICS.md#7-slos-e-thresholds-do-gate-de-ci) via exit code. |

## explain-boundary

Mostra exatamente como um boundary de Shabbat/Yom Tov foi calculado. É a ferramenta
de transparência — sem números mágicos.

```bash
shomer-oncall explain-boundary \
  --date 2026-06-13 \
  --location "America/Sao_Paulo:-23.55:-46.63:760" \
  --shitah gra_8.5 --buffer 18
```

```
shabbat  ·  2026-06-13  ·  America/Sao_Paulo (lat -23.55, lon -46.63, 760 m)
  inicia  2026-06-12T20:14:05+00:00   (shkiah da véspera 2026-06-12 - 18 min de buffer)
  termina 2026-06-13T21:08:29+00:00   (tzais, gra_8.5: 8.5 graus de depression)
  fallback: não
```

| Flag | Default | Significado |
|---|---|---|
| `--date DATE` | *(obrigatório)* | Qualquer data dentro do período; a ferramenta encontra o Shabbat/Yom Tov que a envolve. |
| `--location` | *(obrigatório)* | Ver [sintaxe de location](#sintaxe-de-location). |
| `--shitah` | `gra_8.5` | Opinião de nightfall ([DOMAIN §5](DOMAIN.md#5-opiniões-de-zmanim-shitot)). |
| `--buffer MIN` | `18` | Candle-lighting buffer. |
| `--israel` | (default: diaspora) | Yom Tov de um dia em vez de dois. |

## fairness

Pontua um schedule existente contra as [métricas de fairness](METRICS.md#3-métricas-de-fairness).

```bash
shomer-oncall fairness --schedule out/schedule.json --team ./examples/team.json --gate
```

| Flag | Default | Significado |
|---|---|---|
| `--schedule PATH` | *(obrigatório)* | Um schedule JSON produzido por `schedule`. |
| `--team PATH` | none | Time (para classificar observers no equity gap). |
| `--gate` | off | Exit `4` se os thresholds de fairness forem quebrados. |

## validate

Checagem estática de um arquivo de time sem agendar. Bom como pre-commit hook.

```bash
shomer-oncall validate --team ./examples/team.json
```

Checa: validade de schema, *shitot* resolvíveis, locations parseáveis, time não-vazio,
e avisa se um time todo observante corre risco de períodos de Yom Tov
[uncoverable](ALGORITHMS.md#6-tratando-shifts-uncoverable). Exit `5` em input inválido.

## Sintaxe de location

Uma location é uma string delimitada por dois-pontos: `TZ:lat:lon:elevation_m`.

```
America/Sao_Paulo:-23.55:-46.63:760
Asia/Jerusalem:31.78:35.22:754
Europe/London:51.51:-0.13:35
```

- `TZ` — timezone IANA (usado para exibição e DST; a matemática interna é UTC).
- `lat` / `lon` — graus decimais, sul/oeste negativos.
- `elevation_m` — metros acima do nível do mar; **obrigatório** porque desloca
  materialmente o sunset ([DOMAIN §4](DOMAIN.md#por-que-elevação-e-refração-importam-e-por-que-uma-tabela-não-serve)).

## Exit codes

Projetados para a ferramenta funcionar como gate de CI.

| Código | Significado | Quando |
|---|---|---|
| `0` | Sucesso | Schedule produzido; gate (se ativo) passou. |
| `1` | Erro de uso | Flags inválidas / arquivo ilegível / `--to` antes de `--from`. |
| `2` | **Violação hard** | Uma atribuição quebrou um restricted interval. Nunca deveria ocorrer; indica bug. |
| `3` | Shift uncovered | Um shift não teve membro feasible. ([ALGORITHMS §6](ALGORITHMS.md#6-tratando-shifts-uncoverable)) |
| `4` | Fairness abaixo do threshold | `--gate` ativo e Jain/spread/gap quebrados. |
| `5` | Input inviável / inválido | *shitah* desconhecida, time impossível de parsear, roster vazio. |

## Arquivo de config

`shomer.toml` opcional define defaults para as flags ficarem curtas. As flags
sobrescrevem o arquivo.

```toml
[defaults]
policy   = "daily"
handoff_hour_local = 10

[weights]
base          = 1.0
weekend_mult  = 2.0
holiday_mult  = 1.5
night_mult    = 1.25

[gate]
jain_min       = 0.95
spread_max     = 3.0
equity_gap_max = 0.05
```

Todo threshold e weight fica aqui; nada é hard-coded no binário. É a mesma config que
o [gate de CI](METRICS.md#7-slos-e-thresholds-do-gate-de-ci) lê.
