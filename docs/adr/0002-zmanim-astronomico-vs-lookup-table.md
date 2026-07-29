# ADR-0002: Calcular zmanim astronomicamente, não por lookup table

- **Status:** Aceito
- **Data:** 2026-01-06
- **Decisores:** mantenedores

## Contexto

Boundaries de Shabbat/Yom Tov dependem do *shkiah* (sunset) e do *tzais* (nightfall),
que são funções de data, latitude, longitude, **elevação** e refração atmosférica
([DOMAIN §4](../DOMAIN.md#4-zmanim-transformando-um-dia-em-instants)). Duas formas de
obtê-los:

1. **Lookup table** - enviar tempos de candle-lighting/nightfall pré-computados por
   cidade.
2. **Cálculo astronômico** - derivar de um modelo solar em tempo de execução.

Lookup tables são simples mas carregam suposições escondidas: uma elevação chumbada,
um modelo de refração, uma *shitah*, um conjunto fixo de cidades e um horizonte de
datas além do qual param de ser mantidas em silêncio. Um membro que viaja, trabalha
em altitude ou usa outra *shitah* recebe um boundary **errado** sem nenhum indício.

## Decisão

Calcular todos os *zmanim* astronomicamente em runtime **a partir de primeiros
princípios em Python puro** (o modelo solar padrão "sunrise equation", estilo NOAA),
parametrizado pela location exata do membro (incluindo elevação, via a correção de
horizon dip) e pela *shitah* escolhida. Nenhum boundary é lido de uma tabela estática
por cidade, e nenhuma biblioteca de astronomia/calendário de terceiros é exigida em
runtime - o calendário hebraico também é implementado in-house (aritmética de Hillel).
É o que torna a ferramenta zero-dependency, offline e determinística; a corretude é
garantida não por confiar numa biblioteca, mas por golden tests contra fontes
autoritativas.

## Consequências

**Bom**
- Correto para qualquer location, elevação e data sem refresh de tabela.
- Totalmente explicável: os inputs de cada boundary são explícitos, não implícitos.
- A *shitah* vira um parâmetro limpo ([ADR-0003](0003-shitah-como-parametro.md)).
- Determinismo preservado porque o cálculo é in-house e offline.

**Ruim / custo**
- Somos donos do modelo solar, então a precisão dele é responsabilidade nossa. O
  modelo NOAA de baixa precisão é preciso a poucos minutos; quantificamos isso com a
  [métrica de acurácia de boundary](../METRICS.md#5-acurácia-de-boundary) (erro p95
  ≤ 5 min, bem abaixo do candle-lighting buffer de 18 min, então não pode causar uma
  violação real). Um modelo de maior precisão pode ser trocado atrás da mesma
  interface, e os golden tests guardariam a mudança.
- Latitudes altas podem não ter *tzais* angular no verão; exige um fallback de
  fixed-minutes documentado, sinalizado no rationale
  ([DOMAIN edge case 5](../DOMAIN.md#7-edge-cases-que-o-modelo-precisa-sobreviver)).

## Alternativas consideradas

- **Tabela + fallback astronômico:** mais peças móveis, dois caminhos de código para
  testar, e as suposições da tabela ainda enganariam quando ela "vencesse". Rejeitado.
- **Serviço astronômico ao vivo:** quebra o determinismo offline e adiciona uma
  dependência de rede. Rejeitado ([SECURITY](../SECURITY.md#1-threat-model)).
