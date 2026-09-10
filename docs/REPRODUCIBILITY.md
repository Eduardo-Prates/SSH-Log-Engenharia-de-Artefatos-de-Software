# Protocolo de reprodutibilidade

## Alegações verificadas

O protocolo reproduz quatro alegações centrais do artefato:

1. a suíte automatizada é aprovada;
2. cinco falhas do mesmo IP em até 300 segundos produzem um alerta;
3. elevar o limiar para seis elimina esse alerta;
4. uma janela entre 31 de dezembro e 1º de janeiro recebe anos consecutivos.

O teste de volume incluído na suíte também confirma que 10.000 linhas sintéticas
produzem 1.000 eventos e dez alertas independentes.

## Ambiente mínimo

- CPU e memória suficientes para executar Python; não há requisitos especiais de
  hardware;
- Windows, Linux ou macOS;
- Python 3.11, 3.12, 3.13 ou 3.14;
- Git e acesso ao repositório apenas para aquisição inicial;
- nenhuma dependência externa em tempo de execução.

O CI executa em Linux. A instalação e a demonstração também foram validadas no
Windows com PowerShell e Python 3.14.

## Aquisição e instalação

```text
git clone https://github.com/Eduardo-Prates/SSH-Log-Sentinel---Engenharia-de-Artefatos-de-Software.git
cd SSH-Log-Sentinel---Engenharia-de-Artefatos-de-Software
python -m venv .venv
```

Ative o ambiente no PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install .
```

Ou em Linux e macOS:

```bash
source .venv/bin/activate
python -m pip install .
```

## Reprodução em um comando

```text
python scripts/reproduce.py
```

Saída final esperada:

```text
REPRODUÇÃO CONCLUÍDA
- suíte automatizada: OK
- alerta principal: 192.0.2.50, 5 tentativas
- cenário abaixo do limiar: 0 alertas
- virada do ano: 2027-01-01T00:00:00+00:00
```

O comando retorna código zero somente se todas as alegações forem confirmadas.
O tempo de execução não é usado como critério científico, pois varia entre
ambientes.

## Dados e segurança

Todas as entradas são sintéticas. Os IPs pertencem a faixas reservadas para
documentação, e nenhum segredo ou dado pessoal é necessário. A ferramenta lê os
logs e produz eventos ou alertas; não altera firewall nem bloqueia endereços.

