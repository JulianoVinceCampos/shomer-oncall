# Changelog

Todas as mudanças notáveis deste projeto são documentadas aqui.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Adicionado
- Conjunto completo de documentação (em PT-BR, termos técnicos em inglês):
  arquitetura, domain model, algoritmos, métricas, observabilidade, estratégia de
  testes e ADRs 0001-0006, com diagramas Mermaid (C4, sequência, state machine,
  flowchart de boundary, ERD).
- **Implementação funcional, zero dependências de runtime:**
  - Calendário hebraico (aritmética de Hillel) e *zmanim* solares (modelo NOAA)
    calculados a partir de primeiros princípios em stdlib puro.
  - Calendar engine produzindo restricted intervals canônicos e merged; opinion
    registry (*shitot*); classificação de Yom Tov diaspora-aware.
  - Geração de shifts, feasibility filter e allocator justo determinístico
    (weighted least-loaded greedy + local search redutor de variância).
  - Métricas de fairness/coverage (Jain, Gini, spread, equity gap) e audit trail.
  - CLI: `schedule`, `explain-boundary`, `fairness`, `validate` com exit codes
    documentados; exporters iCal + JSON canônico.
- Suíte de testes: 77 testes (unit, golden anchors de calendário, property tests via
  Hypothesis, contrato de determinismo, e2e de CLI) com ~96% de coverage; ruff +
  mypy-strict limpos; CI GitHub Actions em Python 3.11-3.13.

### Notas
- O install de runtime requer apenas Python 3.11+. Extras opcionais: `yaml` (arquivos
  de time em YAML), `dev` (tooling de teste/lint). Ver `docs/ROADMAP.md` para os
  próximos passos.

[Unreleased]: https://example.com/shomer-oncall/compare/main...HEAD
