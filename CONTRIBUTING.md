# Contribuindo

Obrigado por considerar contribuir. Este projeto tem um viés forte para **corretude,
determinismo e raciocínio documentado**. Algumas normas mantêm isso.

## Regras básicas

1. **Determinismo é inegociável.** Qualquer mudança que possa afetar a saída de
   scheduling deve manter o [contrato de determinismo](docs/TESTING.md#4-contrato-de-determinismo)
   verde. Se sua mudança é inerentemente não-determinística, é a mudança errada.
2. **Opiniões haláchicas são parâmetros, nunca hard-codes.** Se precisar de uma nova
   opinião de *zmanim*, adicione-a ao opinion registry com uma citação - não faça
   branch por ela no allocator.
3. **Todo boundary deve permanecer explicável.** Se você mexer no calendar engine, a
   saída do `explain-boundary` deve continuar dando conta do instant calculado.
4. **Decisões são registradas.** Escolhas de design não-triviais vão para um ADR
   (`docs/adr/`), seguindo o template existente.

## Setup de desenvolvimento

```bash
pip install -e ".[dev]"     # zero deps de runtime; extras de dev para testes/lint
pytest                      # unit + property + golden + determinism
ruff check .                # lint
mypy src                    # types
```

## Definition of done

- [ ] Testes adicionados/atualizados; `pytest` verde incluindo as suítes property e golden.
- [ ] `ruff` e `mypy` limpos.
- [ ] Mudança de comportamento público refletida em `docs/` e no `CHANGELOG.md`.
- [ ] Contrato de determinismo verificado (`pytest -m determinism`).
- [ ] Se a mudança altera uma decisão de design, um ADR é adicionado ou substituído.

## Estilo de commit

Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
Mantenha os PRs focados; uma preocupação por PR.

## Reportando bugs de domínio

Um "bug de domínio" é quando um boundary ou holiday calculado discorda de uma fonte
autoritativa. Inclua: data, location (lat/lon/elevação), *shitah* escolhida, instant
esperado + fonte, e a saída real do `explain-boundary`. São os issues de maior
prioridade.
