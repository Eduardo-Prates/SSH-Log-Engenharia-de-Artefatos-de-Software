# Roteiro de demonstração

Este roteiro apresenta o artefato em aproximadamente cinco minutos. Execute os
comandos no PowerShell, a partir da raiz do repositório, com o ambiente virtual
ativado e o pacote instalado.

## 1. Apresentar o problema

Explique que a inspeção manual de logs OpenSSH dificulta perceber várias falhas
do mesmo IP em pouco tempo. O artefato transforma falhas por senha em eventos
estruturados e aplica uma heurística configurável, sem bloquear IPs.

## 2. Mostrar uma entrada

```powershell
Get-Content .\examples\sample-brute-force.log
```

Destaque as cinco falhas de `192.0.2.50` e a linha de autenticação aceita, que
fica fora do subconjunto analisado.

## 3. Executar somente o parser

```powershell
ssh-log-sentinel .\teste-auth.log --year 2026 --utc-offset=-03:00
```

Mostre os campos `username`, `source_ip`, `invalid_user` e `occurred_at`. O
resumo esperado é `reconhecidas=2 ignoradas=2`, com código de saída zero.

## 4. Detectar o cenário de força bruta

```powershell
ssh-log-sentinel .\examples\sample-brute-force.log `
  --year 2026 --utc-offset=-03:00 --detect
$LASTEXITCODE
```

O alerta esperado identifica `192.0.2.50`, cinco tentativas e quatro usuários.
O código `1` significa que houve alerta; não representa falha interna.

## 5. Demonstrar configuração

```powershell
ssh-log-sentinel .\examples\sample-brute-force.log `
  --year 2026 --utc-offset=-03:00 --detect --threshold 6
$LASTEXITCODE
```

Com limiar seis, o resumo deve informar zero alertas e o código deve ser zero.

## 6. Demonstrar virada de ano

```powershell
ssh-log-sentinel .\examples\sample-year-rollover.log `
  --year 2026 --detect --threshold 2 --window-seconds 60
```

Mostre que a janela começa em `2026-12-31T23:59:30+00:00` e termina em
`2027-01-01T00:00:00+00:00`.

## 7. Encerrar com as evidências

```powershell
ruff check --no-cache .
ruff format --no-cache --check .
python -m unittest discover -s tests -v
```

Mostre também a execução verde do workflow CI no GitHub. Finalize ressaltando
que o detector sinaliza um padrão possível, não confirma comprometimento e não
executa qualquer resposta automática.

