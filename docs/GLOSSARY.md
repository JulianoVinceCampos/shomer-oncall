# Glossário

> Termos de domínio, definidos uma vez. Termos hebraicos/haláchicos são
> transliterados e mantidos assim (em vez de traduzidos) porque a transliteração é o
> termo técnico. Onde um termo tem múltiplas definições válidas, isso é notado e a
> ferramenta o trata como [parâmetro](adr/0003-shitah-como-parametro.md).

## Calendário e observância

**Shabbat (שבת)** - o Sábado judaico. Começa na sexta ao pôr do sol (com um buffer
costumeiro) e termina no sábado ao anoitecer. Trabalho - incluindo agir sobre um page
- é restrito. O período restrito de alta frequência.

**Yom Tov (יום טוב), pl. Yamim Tovim** - um dia de festival judaico maior com
restrições de trabalho similares ao Shabbat: Rosh Hashanah, Yom Kippur, Sukkot (dias
1-2, Shemini Atzeret, Simchat Torah), Pesach (primeiro e último dias), Shavuot.

**Chol HaMoed (חול המועד)** - os dias intermediários de Sukkot e Pesach. Muitos tipos
de trabalho são permitidos; a ferramenta os trata como restrição **opt-in**, off por
padrão.

**Fast day (dia de jejum)** - ex. Tisha B'Av, Yom Kippur. Agir sobre um page em geral
é permitido, então a ferramenta os modela como disponibilidade *soft* (deprioriza) em
vez de bloqueio hard - opt-in.

**Diaspora** - comunidades judaicas fora da terra de Israel, onde a maioria dos
*Yamim Tovim* é observada por **dois dias** em vez de um. Uma flag por time/por
membro; errá-la sub-bloqueia em silêncio um observante no exterior.

**Calendário lunisolar** - um calendário cujos meses acompanham a lua e cujos anos
acompanham o sol, re-sincronizados inserindo um mês bissexto. O calendário hebraico é
lunisolar, e é por isso que as datas dos festivais se movem contra o gregoriano.

**Adar I (אדר א׳)** - o mês bissexto adicionado em 7 de cada 19 anos para manter o
calendário lunisolar alinhado ao ano solar. Sua presença desloca as datas gregorianas
dos festivais de primavera.

**Observant / observante** - neste projeto, um membro do time que declara uma ou mais
categorias restritas (`observes`). "Non-observer" significa um membro sem restrições
de calendário declaradas - não carrega nenhum outro significado aqui.

## Zmanim (horas haláchicas)

**Zmanim (זמנים)** - "tempos"; horas haláchicas do dia derivadas da posição do sol
(dawn, sunrise, midday, sunset, nightfall etc.).

**Shkiah (שקיעה)** - pôr do sol; o momento em que a borda superior do sol cai abaixo
do horizonte real, corrigido por refração atmosférica e elevação do observador. Marca
o início do Shabbat/Yom Tov (antes do candle-lighting buffer).

**Tzais / Tzais hakochavim (צאת הכוכבים)** - anoitecer, literalmente "a saída das
estrelas". Marca o *fim* do Shabbat/Yom Tov. Definido ou como o sol atingindo um
**depression angle** abaixo do horizonte ou como um número fixo de **minutos** após o
sunset - o valor mais dependente de opinião no sistema.

**Candle-lighting buffer** - o intervalo costumeiro *antes* do pôr do sol em que se
entra no Shabbat (comumente 18 minutos; 40 em algumas comunidades). A ferramenta
inicia o restricted interval em `shkiah − buffer`.

**Shitah (שיטה), pl. shitot** - uma "opinião" ou método haláchico. Aqui, um conjunto
nomeado de parâmetros de cálculo de *zmanim* (ex. qual depression angle define o
*tzais*) mais uma citação. Selecionado por membro; vive só no
[opinion registry](DOMAIN.md#5-opiniões-de-zmanim-shitot).

**Posek (פוסק), pl. poskim** - uma autoridade rabínica que decide questões de lei
judaica. Diferentes *poskim* geram diferentes *shitot* - daí a ferramenta nunca
hard-codar uma.

**Psak (פסק)** - uma decisão haláchica. A ferramenta se remete ao *psak* da
comunidade expondo a *shitah* como configuração.

**GRA** - o Vilna Gaon (Rabbi Eliyahu de Vilna); a escola dele fundamenta as opiniões
comuns de *tzais* por graus (`gra_*`).

**Magen Avraham (MGA)** - uma autoridade clássica associada a cálculos de tempo mais
stringent; fundamenta as opiniões `mga_*`.

**Rabbeinu Tam** - uma autoridade cuja opinião gera um *tzais* notavelmente tarde
(72 minutos / 16.1°), a opção mais stringent do registry.

**Depression angle** - quão longe (em graus) o centro do sol está abaixo do horizonte.
Opiniões de twilight/nightfall são muitas vezes expressas como um depression angle
(ex. 8.5°).

## Scheduling e fairness

**Shift** - um slot de plantão delimitado (um dia, uma semana, ou um bloco
follow-the-sun) que recobre a window inteira sem gaps.

**Restricted interval** - um intervalo de tempo em UTC durante o qual um membro
específico não pode ser paginado, derivado de sua observância + location + *shitah*.
Canonicamente sorted, merged, não-adjacente.

**Feasible pair** - um `(membro, shift)` onde o shift não intersecta nenhum restricted
interval do membro. Só pares feasible podem ser atribuídos.

**Load weight** - o burden score de um shift (`w(s)`), refletindo quão exigente é
(multiplicadores weekend/holiday/night). Fairness é medida em weight, não em contagem.

**Weighted load `L(m)`** - a soma dos weights dos shifts atribuídos ao membro `m`.

**History carry-in `H(m)`** - a load de um membro carregada de windows anteriores,
para a fairness ser avaliada num rolling horizon em vez de resetar a cada período.

**Weighted spread** - `max load − min load` no time; a quantidade que o allocator
minimiza.

**Jain's fairness index** - uma medida de fairness limitada em `(0, 1]`; `1.0`
significa loads iguais. Ver [METRICS §3.1](METRICS.md#31-jains-fairness-index).

**Gini coefficient** - uma medida de desigualdade em `[0, 1]`; `0` significa igualdade
perfeita. Ver [METRICS §3.2](METRICS.md#32-gini-coefficient).

**Equity gap** - a diferença de load média entre observers e non-observers; a métrica
que prova que a ferramenta equilibra a carga em vez de despejar fins de semana nos
non-observers. Ver [METRICS §3.4](METRICS.md#34-equity-gap-observer--non-observer).

**Uncoverable shift** - um shift cujo conjunto feasible é vazio; nunca descartado em
silêncio, sempre reportado ([ALGORITHMS §6](ALGORITHMS.md#6-tratando-shifts-uncoverable)).

## Engenharia

**Functional core, imperative shell** - o padrão em que toda a lógica são funções
puras (o core) envoltas por uma camada fina de I/O (o shell). Habilita determinismo e
testes sem mocks. Ver [ARCHITECTURE §1](ARCHITECTURE.md#1-visão-geral).

**Contrato de determinismo** - a garantia forçada de que inputs idênticos produzem
saída byte-idêntica. Ver [TESTING §4](TESTING.md#4-contrato-de-determinismo).

**Audit trail** - o registro machine-readable do *porquê* de cada boundary e
atribuição; autoritativo sobre os logs. Ver [OBSERVABILITY §2](OBSERVABILITY.md#2-audit-trail).

**Golden fixture** - um par input→esperado congelado, checado contra uma fonte externa
autoritativa. Ver [TESTING §2](TESTING.md#2-golden-fixtures).

**ILP (integer linear program)** - a forma de otimização exata que o allocator resolve
opcionalmente (regime `exact`). Ver [ALGORITHMS §5](ALGORITHMS.md#5-alocação).
