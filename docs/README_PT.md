<p align="center">
  <img src="../image/banner.png" width="700" alt="Codex Autoresearch">
</p>

<h2 align="center"><b>Aim. Iterate. Arrive.</b></h2>

<p align="center">
  <i>Motor de experimentacao autonoma orientada por objetivos para o Codex.</i>
</p>

<p align="center">
  <a href="https://developers.openai.com/codex/skills"><img src="https://img.shields.io/badge/Codex-Skill-blue?logo=openai&logoColor=white" alt="Codex Skill"></a>
  <a href="https://github.com/leo-lilinxiao/codex-autoresearch"><img src="https://img.shields.io/github/stars/leo-lilinxiao/codex-autoresearch?style=social" alt="GitHub Stars"></a>
  <a href="../LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License"></a>
</p>

<p align="center">
  <a href="../README.md">English</a> ·
  <a href="README_ZH.md">中文</a> ·
  <a href="README_JA.md">日本語</a> ·
  <a href="README_KO.md">한국어</a> ·
  <a href="README_FR.md">Français</a> ·
  <a href="README_DE.md">Deutsch</a> ·
  <a href="README_ES.md">Español</a> ·
  <b>Português</b> ·
  <a href="README_RU.md">Русский</a>
</p>

<p align="center">
  <a href="#inicio-rapido">Inicio rapido</a> ·
  <a href="#o-que-faz">O que faz</a> ·
  <a href="#arquitetura">Arquitetura</a> ·
  <a href="#modos">Modos</a> ·
  <a href="#configuracao">Configuracao</a> ·
  <a href="../GUIDE.md">Guia de operacao</a> ·
  <a href="../EXAMPLES.md">Receitas</a>
</p>

---

## Inicio rapido

**1. Instalacao:**

```bash
git clone https://github.com/leo-lilinxiao/codex-autoresearch.git
cp -r codex-autoresearch your-project/.agents/skills/codex-autoresearch
```

Ou use o skill installer no Codex:
```text
$skill-installer install https://github.com/leo-lilinxiao/codex-autoresearch
```

**2. Abra o Codex no seu projeto e diga o que voce quer fazer:**

```text
$codex-autoresearch
Quero eliminar todos os tipos `any` do meu codigo TypeScript
```

**3. O Codex escaneia, confirma e depois itera de forma autonoma:**

```
Codex: Encontrei 47 ocorrencias de `any` em src/**/*.ts.

       Confirmado:
       - Objetivo: eliminar os tipos `any` em src/**/*.ts
       - Metrica: quantidade de `any` (atual: 47), direcao: reduzir
       - Verificacao: grep + tsc --noEmit como guarda

       Preciso confirmar:
       - Executar ate eliminar todos, ou limitar a N iteracoes?

       Responda "go" para comecar, ou me diga o que alterar.

Voce:  go, roda a noite toda.

Codex: Iniciando -- linha de base: 47. Iterando ate ser interrompido.
```

As melhorias se acumulam. As falhas sao revertidas. Tudo fica registrado.

Mais opcoes de instalacao em [INSTALL.md](../INSTALL.md). Manual completo em [GUIDE.md](../GUIDE.md).

---

## O que faz

Um skill do Codex que executa um loop de "modificar-verificar-decidir" no seu codigo. Cada iteracao faz uma alteracao atomica, verifica contra uma metrica mecanica e mantem ou descarta o resultado. O progresso se acumula no git; falhas sao revertidas automaticamente. Funciona com qualquer linguagem, qualquer framework, qualquer objetivo mensuravel.

Inspirado nos principios do [autoresearch do Karpathy](https://github.com/karpathy/autoresearch), generalizado para alem de ML.

### Por que existe

O autoresearch do Karpathy provou que um loop simples -- modificar, verificar, manter ou descartar, repetir -- pode levar um treinamento de ML da linha de base a novos patamares durante a noite. codex-autoresearch generaliza esse loop para tudo em engenharia de software que tenha um numero. Cobertura de testes, erros de tipo, latencia de performance, avisos de lint -- se existe uma metrica, pode iterar de forma autonoma.

---

## Arquitetura

```
                    +------------------+
                    |   Ler contexto   |
                    +--------+---------+
                             |
                    +--------v---------+
                    | Estabelecer linha|  <-- iteracao #0
                    |      de base     |
                    +--------+---------+
                             |
              +--------------v--------------+
              |                             |
              |    +-------------------+    |
              |    | Escolher hipotese |    |
              |    +--------+----------+    |
              |             |               |
              |    +--------v----------+    |
              |    | Fazer UMA mudanca |    |
              |    +--------+----------+    |
              |             |               |
              |    +--------v----------+    |
              |    |   git commit      |    |
              |    +--------+----------+    |
              |             |               |
              |    +--------v----------+    |
              |    | Executar verif.   |    |
              |    +--------+----------+    |
              |             |               |
              |          Melhorou?          |
              |        /         \          |
              |      sim          nao       |
              |      /              \        |
              | +---v----+    +-----v----+  |
              | | MANTER |    | REVERTER |  |
              | +---+----+    +-----+----+  |
              |      \            /          |
              |    +--v----------v--+       |
              |    | Registrar res. |       |
              |    +-------+--------+       |
              |            |                |
              +------------+ (repetir)      |
              |                             |
              +-----------------------------+
```

O loop executa ate ser interrompido (sem limite) ou exatamente N iteracoes (limitado via `Iterations: N`).

**Pseudocodigo:**

```
LOOP (para sempre ou N vezes):
  1. Revisar estado atual + historico git + registro de resultados
  2. Escolher UMA hipotese (baseada no que funcionou, no que falhou, no que nao foi testado)
  3. Fazer UMA alteracao atomica
  4. git commit (antes da verificacao)
  5. Executar verificacao mecanica
  6. Melhorou -> manter. Piorou -> git reset. Quebrou -> corrigir ou pular.
  7. Registrar o resultado
  8. Repetir. Nunca parar. Nunca perguntar.
```

---

## Modos

Seis modos, um unico padrao de invocacao: `$codex-autoresearch` seguido de uma frase descrevendo o que voce quer. O Codex detecta automaticamente o modo e guia voce atraves de uma breve conversa para completar a configuracao.

| Modo | Quando usar | Para quando |
|------|-------------|-------------|
| `loop` | Voce tem um objetivo mensuravel para otimizar | Interrupcao ou N iteracoes |
| `plan` | Voce tem um objetivo mas nao a configuracao | Bloco de configuracao gerado |
| `debug` | Voce precisa de analise de causa raiz com evidencia | Todas as hipoteses testadas ou N iteracoes |
| `fix` | Algo esta quebrado e precisa de reparo | Contagem de erros chega a zero |
| `security` | Voce precisa de uma auditoria estruturada de vulnerabilidades | Todas as superficies de ataque cobertas ou N iteracoes |
| `ship` | Voce precisa de verificacao de lancamento com portoes | Todos os itens da lista aprovados |

**Selecao rapida:**

```
"Quero melhorar X"              -->  loop (ou plan se nao tem certeza da metrica)
"Algo esta quebrado"            -->  fix  (ou debug se a causa e desconhecida)
"Esse codigo e seguro?"         -->  security
"Pronto para lancar"            -->  ship
```

---

## Configuracao

### Campos obrigatorios (modo `loop`)

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `Goal` | Objetivo a alcancar | `Reduce type errors to zero` |
| `Scope` | Globs de arquivos a modificar | `src/**/*.ts` |
| `Metric` | Numero a rastrear | `type error count` |
| `Direction` | `higher` ou `lower` | `lower` |
| `Verify` | Comando que produz a metrica | `tsc --noEmit 2>&1 \| wc -l` |

### Campos opcionais

| Campo | Valor padrao | Proposito |
|-------|--------------|-----------|
| `Guard` | nenhum | Comando de seguranca que sempre deve passar (prevencao de regressoes) |
| `Iterations` | ilimitado | Limitar a N iteracoes |
| `Run tag` | automatico | Rotulo para esta execucao |
| `Stop condition` | nenhum | Regra personalizada de parada antecipada |

Quando faltam campos obrigatorios, um assistente interativo escaneia seu repositorio e sempre confirma com voce antes de iniciar (ate 5 rodadas). Voce nao precisa conhecer os nomes dos campos.

### Verificacao de duplo portao

Dois comandos com funcoes distintas:

- **Verify** = "A metrica alvo melhorou?" (mede o progresso)
- **Guard** = "Algo mais quebrou?" (previne regressoes)

```text
Verify: pytest --cov=src --cov-report=term 2>&1 | grep TOTAL | awk '{print $NF}'   # a cobertura subiu?
Guard: npx tsc --noEmit                                                              # os tipos ainda passam?
```

Se verify passa mas guard falha, a alteracao e reajustada (ate 2 tentativas) e depois revertida. Os arquivos de Guard nunca sao modificados.

---

## Guia de decisao rapida

| Voce quer... | Modo | Configuracao chave |
|--------------|------|--------------------|
| Empurrar um numero em uma direcao a noite toda | `loop` | Goal + Metric + Verify |
| Descobrir qual metrica rastrear | `plan` | Apenas um Goal |
| Encontrar por que algo esta quebrado | `debug` | Scope + Symptom |
| Fazer tests/tipos/lint passarem | `fix` | Comando Target |
| Auditar codigo em busca de vulnerabilidades | `security` | Scope + Focus |
| Lancar com confianca | `ship` | Diga "lancar" ou "primeiro um ensaio" |

---

## Detalhes dos modos

### loop

Modo padrao. Itera em direcao a um objetivo mensuravel.

```
Voce:  Elimine todos os tipos `any` do meu codigo TypeScript

Codex: Encontrei 47 `any` em src/**/*.ts.

       Confirmado:
       - Objetivo: eliminar todos os tipos `any`
       - Metrica: quantidade de `any` (atual: 47), direcao: reduzir
       - Verificacao: grep count, Guard: tsc --noEmit

       Preciso confirmar:
       - Executar ate zero, ou limitar a N iteracoes?

       Responda "go" para comecar.

Voce:  go, a noite toda.
```

### plan

Converte um objetivo vago em uma configuracao de loop validada.

```
Voce:  Quero que nossa API seja mais rapida mas nao sei por onde comecar

Codex: Escaneei o repositorio. A camada API esta em src/api/ com Express + Prisma.

       Preciso confirmar:
       - O que importa mais: latencia p95, throughput ou cold start?
       - Fazer benchmark de toda a API ou de endpoints especificos?

       Me diga sua prioridade.

Voce:  Latencia p95, o endpoint /search e o pior.
```

### debug

Caca de bugs baseada em evidencia. Cada iteracao testa uma hipotese falsificavel.

```
Voce:  Nossa API retorna 503 aleatoriamente sob carga, nao sei por que

Codex: Vejo connection pooling em src/db/pool.ts, rate limiting em src/middleware/,
       e 3 handlers assincronos sem limites de erro.

       Confirmado:
       - Sintoma: 503 intermitentes sob carga concorrente
       - Escopo: src/api/, src/db/, src/middleware/

       Preciso confirmar:
       - Quando comecou? Depois de uma mudanca especifica, ou sempre?
       - Se eu encontrar a causa, tambem corrijo?

       Me de contexto.

Voce:  Comecou depois da refatoracao do connection pool semana passada. Primeiro encontre a causa.
```

### fix

Repara erros iterativamente ate a contagem chegar a zero.

```
Voce:  pytest esta falhando, 12 testes quebrados depois da refatoracao

Codex: Vejo 12 falhas em tests/.

       Confirmado:
       - Objetivo: fazer todos os testes do pytest passarem
       - Atual: 12 falhas

       Preciso confirmar:
       - Tambem usar ruff como guarda para evitar introduzir problemas de lint?
       - Corrigir todos os 12, ou focar em um modulo primeiro?

       Responda "go" para comecar.

Voce:  Corrige todos, sim usa ruff como guarda. Go.
```

### security

Auditoria somente leitura STRIDE + OWASP + red team. Cada achado requer evidencia em codigo.

```
Voce:  Verifique nossa API em busca de vulnerabilidades de injecao

Codex: Confirmado:
       - Escopo: src/api/ e src/middleware/ (14 arquivos)
       - Foco: injecao SQL, XSS, sanitizacao de entrada

       Preciso confirmar:
       - Apenas relatorio, ou tambem corrigir achados criticos?
       - Tambem cobrir autenticacao/controle de acesso?

       Me diga sua preferencia.

Voce:  Primeiro o relatorio, e sim cobre autenticacao tambem.
```

### ship

Verificacao de lancamento com portoes. Detecta automaticamente o que voce esta lancando (PR, deploy, release).

```
Voce:  Lancar

Codex: Detectado: PR para main com 3 commits.

       Confirmado:
       - Tipo: PR de codigo
       - Destino: branch main

       Preciso confirmar:
       - Primeiro um ensaio ou direto em producao?
       - Monitoramento pos-lancamento? (5 min / 15 min / pular)

       Me diga sua preferencia.

Voce:  Primeiro um ensaio.
```

Consulte [GUIDE.md](../GUIDE.md) para uso detalhado e opcoes avancadas de cada modo.

---

## Combinacao de modos

Os modos podem ser compostos sequencialmente:

```
plan  -->  loop              # primeiro gerar configuracao, depois executar
debug -->  fix               # primeiro encontrar bugs, depois corrigi-los
security + fix               # auditar e remediar em um so passo
```

---

## Registro de resultados

Cada iteracao e registrada em formato TSV (`research-results.tsv`):

```
iteration  commit   metric  delta   status    description
0          a1b2c3d  47      0       baseline  initial any count
1          b2c3d4e  41      -6      keep      replace any in auth module with strict types
2          -        49      +8      discard   generic wrapper introduced new anys
3          c3d4e5f  38      -3      keep      type-narrow API response handlers
```

Um resumo de progresso e impresso a cada 5 iteracoes. Execucoes limitadas imprimem um resumo final de linha de base ao melhor valor.

---

## Modelo de seguranca

| Preocupacao | Como e tratada |
|-------------|----------------|
| Diretorio de trabalho sujo | O loop se recusa a iniciar; sugere modo `plan` ou branch limpa |
| Alteracao com falha | `git reset --hard HEAD~1` mantem o historico limpo; o registro de resultados e a trilha de auditoria |
| Falha do Guard | Ate 2 tentativas de reajuste, depois reverte |
| Erro de sintaxe | Correcao imediata, nao conta como iteracao |
| Crash em tempo de execucao | Ate 3 tentativas de correcao, depois pula |
| Esgotamento de recursos | Reverte, tenta uma variante menor |
| Processo travado | Encerra apos timeout, reverte |
| Preso (5+ descartes consecutivos) | Rele todo o contexto, revisa padroes, tenta mudancas mais ousadas |
| Ambiguidade durante o loop | Aplica melhores praticas de forma autonoma; nunca para para perguntar ao usuario |
| Efeitos colaterais externos | O modo `ship` requer confirmacao explicita durante o assistente de pre-lancamento |

---

## Estrutura do projeto

```
codex-autoresearch/
  SKILL.md                          # ponto de entrada do skill (carregado pelo Codex)
  README.md                         # documentacao em ingles
  INSTALL.md                        # guia de instalacao
  GUIDE.md                          # manual de operacao
  EXAMPLES.md                       # receitas por dominio
  CONTRIBUTING.md                   # guia de contribuicao
  LICENSE                           # MIT
  agents/
    openai.yaml                     # metadados do Codex UI
  image/
    banner.png                      # banner do projeto
  docs/
    README_ZH.md                    # chines
    README_JA.md                    # japones
    README_KO.md                    # coreano
    README_FR.md                    # frances
    README_DE.md                    # alemao
    README_ES.md                    # espanhol
    README_PT.md                    # este arquivo
    README_RU.md                    # russo
  scripts/
    validate_skill_structure.sh     # script de validacao de estrutura
  references/
    autonomous-loop-protocol.md     # especificacao do protocolo de loop
    core-principles.md              # principios universais
    plan-workflow.md                # especificacao do modo plan
    debug-workflow.md               # especificacao do modo debug
    fix-workflow.md                 # especificacao do modo fix
    security-workflow.md            # especificacao do modo security
    ship-workflow.md                # especificacao do modo ship
    interaction-wizard.md           # contrato de configuracao interativa
    structured-output-spec.md       # especificacao de formato de saida
    modes.md                        # indice de modos
    results-logging.md              # especificacao de formato TSV
```

---

## FAQ

**Como escolho uma metrica?** Use `Mode: plan`. Ele analisa seu codigo e sugere uma.

**Funciona com qualquer linguagem?** Sim. O protocolo e agnostico a linguagem. Apenas o comando de verificacao e especifico do dominio.

**Como eu paro?** Interrompa o Codex, ou configure `Iterations: N`. O estado do git e sempre consistente porque os commits acontecem antes da verificacao.

**O modo security modifica meu codigo?** Nao. Analise somente leitura. Diga ao Codex "tambem corrija os achados criticos" durante a configuracao para optar pela remediacao.

**Quantas iteracoes?** Depende da tarefa. 5 para correcoes direcionadas, 10-20 para exploracao, ilimitadas para execucoes noturnas.

---

## Agradecimentos

Este projeto se baseia nas ideias do [autoresearch do Karpathy](https://github.com/karpathy/autoresearch). A plataforma de skills do Codex e da [OpenAI](https://openai.com).

---

## Star History

<a href="https://www.star-history.com/?repos=leo-lilinxiao%2Fcodex-autoresearch&type=timeline&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=leo-lilinxiao/codex-autoresearch&type=timeline&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=leo-lilinxiao/codex-autoresearch&type=timeline&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/image?repos=leo-lilinxiao/codex-autoresearch&type=timeline&legend=top-left" />
 </picture>
</a>

---

## Licenca

MIT -- veja [LICENSE](../LICENSE).
