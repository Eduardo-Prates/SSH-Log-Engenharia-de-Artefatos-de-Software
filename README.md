# SSH Log Sentinel

[![CI](https://github.com/Eduardo-Prates/SSH-Log-Sentinel---Engenharia-de-Artefatos-de-Software/actions/workflows/ci.yml/badge.svg)](https://github.com/Eduardo-Prates/SSH-Log-Sentinel---Engenharia-de-Artefatos-de-Software/actions/workflows/ci.yml)

Protótipo acadêmico de uma ferramenta CLI em Python 3.11+ para analisar logs
de autenticação do OpenSSH e, em incrementos futuros, sinalizar possíveis
ataques de força bruta.

O primeiro incremento implementou a leitura de linhas `Failed password`. O
segundo acrescentou timestamps normalizados e um detector independente por
limiar e janela. A CLI ainda não classifica endereços IP nem executa bloqueios.

## Executar localmente

Sem instalar o pacote, no PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m ssh_log_sentinel caminho\para\auth.log
```

A CLI escreve um objeto JSON por tentativa reconhecida na saída padrão e um
resumo de leitura na saída de erro.

Logs no formato tradicional do syslog não trazem ano nem fuso. Para normalizar
esses horários sem fazer suposições implícitas, informe ambos os dados. Exemplo
para um log de 2026 em UTC-3:

```powershell
python -m ssh_log_sentinel caminho\para\auth.log --year 2026 --utc-offset-hours=-3
```

O campo `occurred_at` será emitido em UTC. Sem `--year`, ele será `null` para
linhas syslog; timestamps ISO 8601 são normalizados diretamente.

## Detectar possíveis ataques

O modo de detecção é ativado explicitamente. Por padrão, ele alerta quando o
mesmo IP acumula cinco falhas em até 300 segundos:

```powershell
python -m ssh_log_sentinel .\examples\sample-brute-force.log `
  --year 2026 --utc-offset=-03:00 --detect
```

Limiar e janela podem ser alterados:

```powershell
python -m ssh_log_sentinel .\auth.log --year 2026 --detect `
  --threshold 8 --window-seconds 120
```

No modo `--detect`, a saída padrão contém apenas alertas JSON. O resumo permanece
na saída de erro. Os códigos de saída são apropriados para automação:

- `0`: processamento concluído sem alertas;
- `1`: um ou mais alertas encontrados;
- `2`: erro de entrada, configuração ou dados temporais insuficientes.

O código `1` representa uma detecção válida, não uma falha interna. Logs syslog
exigem `--year` nesse modo. A ferramenta apenas informa alertas; ela não modifica
firewall nem bloqueia IPs.

### Entrada padrão e arquivo de alertas

Use `-` no lugar do arquivo para ler de um pipeline:

```powershell
Get-Content .\auth.log | python -m ssh_log_sentinel - `
  --year 2026 --utc-offset=-03:00 --detect
```

Para gravar os alertas como JSON Lines sem escrevê-los na saída padrão:

```powershell
python -m ssh_log_sentinel .\auth.log --year 2026 --detect `
  --alerts-file .\alerts.jsonl
```

`--alerts-file` requer `--detect`. O arquivo é escrito somente depois que toda a
análise termina sem erro temporal. O antigo `--utc-offset-hours` continua aceito
para compatibilidade, mas `--utc-offset=±HH:MM` também representa fusos como
`-03:30` ou `+05:30`.

### Virada de ano em syslog

Para logs sem ano, `--year` representa o ano do primeiro evento reconhecido. Uma
regressão de calendário superior a 180 dias é interpretada como passagem para o
ano seguinte. O comportamento pode ser conferido com:

```powershell
python -m ssh_log_sentinel .\examples\sample-year-rollover.log `
  --year 2026 --detect --threshold 2 --window-seconds 60
```

## Testes

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

Para instalar também as ferramentas de desenvolvimento e reproduzir todas as
verificações do CI:

```powershell
python -m pip install -e ".[dev]"
ruff check --no-cache .
ruff format --no-cache --check .
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

O workflow em `.github/workflows/ci.yml` executa lint e formatação, além da suíte
em Python 3.11, 3.12, 3.13 e 3.14, a cada `push` e `pull_request`. O teste de
volume gera deterministicamente 10.000 linhas sintéticas; nenhuma amostra real
ou dado pessoal é incorporado.

## Evidências versionadas

- `teste-auth.log`: entrada pequena usada nas validações manuais;
- `alerts-validacao.jsonl`: alerta resultante conferido pelo aluno;
- `examples/`: entradas reproduzíveis dos cenários de força bruta e virada de
  ano.

Todos os endereços utilizados pertencem a faixas reservadas para documentação.

## Limitações conhecidas

- somente mensagens `Failed password` no formato documentado são reconhecidas;
- outros métodos e variantes de mensagens OpenSSH ainda não são analisados;
- logs syslog precisam de ano e fuso fornecidos pelo usuário para detecção;
- a virada de ano usa uma heurística de regressão superior a 180 dias;
- o detector pressupõe ordem cronológica por IP;
- a ferramenta analisa entradas finitas e não acompanha o arquivo em tempo real;
- alertas indicam comportamento possível, não comprovam uma invasão;
- nenhuma alteração de firewall ou bloqueio automático é realizada.

## Documentação acadêmica

- [Arquitetura](docs/ARCHITECTURE.md)
- [Checklist de entrega](docs/DELIVERY_CHECKLIST.md)
- [Especificação](SPEC.md)
- [Relato de uso da IA e decisões](RELATO.txt)

A especificação e os limites de cada incremento estão em [SPEC.md](SPEC.md).
