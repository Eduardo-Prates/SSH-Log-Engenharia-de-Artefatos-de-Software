# SSH Log Sentinel

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

## Testes

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

A especificação e os limites de cada incremento estão em [SPEC.md](SPEC.md).
