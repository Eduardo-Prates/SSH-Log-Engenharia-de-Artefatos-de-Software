# Especificação — SSH Log Sentinel

## 1. Problema

Servidores OpenSSH registram falhas de autenticação, mas a inspeção manual dos
logs é lenta e sujeita a erros. O SSH Log Sentinel será uma ferramenta de linha
de comando capaz de transformar esses registros em eventos estruturados e, em
incrementos posteriores, identificar concentrações de falhas compatíveis com
ataques de força bruta.

## 2. Objetivo do primeiro incremento

Entregar uma base executável e testável que:

1. leia um arquivo de log sem modificá-lo;
2. reconheça falhas de autenticação por senha emitidas pelo `sshd`;
3. normalize os campos necessários para a futura detecção; e
4. ignore com segurança linhas fora do formato suportado.

A detecção por janela de tempo, a geração de alertas e qualquer bloqueio de IP
estão explicitamente fora deste incremento.

## 3. Entradas suportadas

Uma entrada é um arquivo texto com uma linha por registro. Nesta versão, o
parser reconhece mensagens do tipo:

```text
Jan 10 12:34:56 servidor sshd[1234]: Failed password for alice from 192.0.2.10 port 51000 ssh2
Jan 10 12:35:02 servidor sshd[1234]: Failed password for invalid user admin from 2001:db8::10 port 51001 ssh2
```

O prefixo pode usar a data tradicional do syslog (`Mmm d HH:MM:SS`) ou uma data
ISO 8601 iniciada por `AAAA-MM-DDT`. O parser não inventa o ano ausente no
formato tradicional: preserva a data como texto para normalização futura.

Linhas de sucesso (`Accepted ...`), mensagens `Invalid user ...` isoladas e
falhas de métodos diferentes de senha não produzem eventos neste incremento.
Isso evita contar duas vezes a sequência em que o OpenSSH registra primeiro
`Invalid user` e depois `Failed password`.

## 4. Evento normalizado

Para cada linha reconhecida, o parser fornece:

- data/hora textual presente no log;
- hostname;
- PID do `sshd`, quando presente;
- nome de usuário informado;
- indicador de usuário marcado como inválido pelo OpenSSH;
- endereço IP de origem validado como IPv4 ou IPv6;
- porta de origem validada no intervalo de 1 a 65535;
- método de autenticação (`password`); e
- linha original sem a quebra de linha final.

## 5. Requisitos funcionais

- **RF-01:** receber o caminho de um arquivo de log pela CLI.
- **RF-02:** processar o arquivo incrementalmente, sem exigir sua carga completa
  em memória.
- **RF-03:** reconhecer as duas variantes de `Failed password` descritas na
  seção 3, incluindo `invalid user`.
- **RF-04:** validar o IP e a porta antes de criar um evento.
- **RF-05:** emitir um JSON por evento reconhecido e informar quantas linhas
  foram reconhecidas e ignoradas.
- **RF-06:** não alterar o arquivo de entrada nem executar ações de bloqueio.

## 6. Requisitos não funcionais

- **RNF-01:** executar em Python 3.11 ou superior sem dependências de execução
  externas.
- **RNF-02:** separar parsing, modelo de domínio e interface CLI.
- **RNF-03:** manter comportamento determinístico e coberto por testes unitários.
- **RNF-04:** tratar linhas desconhecidas ou malformadas como não reconhecidas,
  sem interromper o processamento.

## 7. Critérios de aceite do primeiro incremento

- **CA-01:** uma falha de senha de usuário existente gera um evento com usuário,
  IP, porta, hostname e PID corretos.
- **CA-02:** uma falha contendo `invalid user` gera um evento com o indicador de
  usuário inválido ativado e sem incorporar essa expressão ao nome do usuário.
- **CA-03:** endereços IPv4 e IPv6 válidos são aceitos.
- **CA-04:** linha de autenticação aceita, IP inválido ou porta fora do intervalo
  retorna nenhum evento e não lança exceção.
- **CA-05:** a leitura de múltiplas linhas mantém somente os eventos suportados e
  preserva a ordem.
- **CA-06:** a suíte automatizada termina com sucesso em Python 3.11+.
- **CA-07:** a CLI processa um arquivo de exemplo e produz JSON válido sem iniciar
  qualquer mecanismo de detecção ou bloqueio.

## 8. Estrutura após o segundo incremento

```text
.
├── pyproject.toml
├── README.md
├── RELATO.txt
├── SPEC.md
├── examples/
│   ├── sample-brute-force.log
│   └── sample-year-rollover.log
├── src/
│   └── ssh_log_sentinel/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── detector.py
│       ├── models.py
│       └── parser.py
└── tests/
    ├── test_cli.py
    ├── test_detector.py
    └── test_parser.py
```

O arquivo `teste-auth.log`, criado durante a validação humana, é uma entrada de
teste local e não faz parte da estrutura exigida da aplicação.

## 9. Segundo incremento — normalização e detector isolado

### 9.1 Escopo

O segundo incremento acrescenta uma linha do tempo inequívoca e a primeira
regra de detecção, sem conectá-la ainda ao comportamento padrão da CLI:

- timestamps ISO 8601 são convertidos para UTC;
- timestamps syslog são convertidos para UTC somente quando o chamador fornece
  o ano e o deslocamento em relação a UTC;
- a CLI aceita `--year` e `--utc-offset-hours` e inclui `occurred_at` no JSON;
- o detector recebe eventos já normalizados e identifica pelo menos `N` falhas
  do mesmo IP em uma janela inclusiva de `T` segundos;
- IPs diferentes mantêm estados independentes;
- um fluxo contínuo gera um único alerta por IP e é rearmado após um intervalo
  sem falhas maior que a janela.

O detector não bloqueia endereços, não altera firewall e ainda não é acionado
pela CLI. Isso permite validar a regra separadamente antes de expô-la ao usuário.

### 9.2 Critérios de aceite

- **CA-08:** um timestamp ISO 8601 com fuso é convertido para UTC.
- **CA-09:** um timestamp syslog só ganha `occurred_at` quando recebe ano; o
  deslocamento fornecido é respeitado na conversão para UTC.
- **CA-10:** o detector alerta ao atingir o limiar dentro da janela, incluindo
  tentativas exatamente nos limites inicial e final.
- **CA-11:** tentativas de IPs diferentes não são somadas.
- **CA-12:** tentativas fora da janela não atingem o limiar.
- **CA-13:** um fluxo contínuo não gera alertas repetidos e um novo fluxo, após
  intervalo maior que a janela, pode gerar novo alerta.
- **CA-14:** eventos sem horário normalizado ou fora de ordem para o mesmo IP são
  rejeitados explicitamente, evitando uma conclusão silenciosamente incorreta.
- **CA-15:** nenhuma ação automática de bloqueio é executada.

## 10. Terceiro incremento — integração opt-in à CLI

### 10.1 Interface

- `--detect` ativa a detecção e faz a saída padrão conter somente alertas JSON;
- `--threshold N` define o número mínimo de falhas, com padrão 5;
- `--window-seconds S` define a janela, com padrão 300 segundos;
- `--year` é obrigatório na prática para detectar sobre timestamps syslog, pois
  eventos sem horário normalizado são recusados;
- `--utc-offset-hours H` informa o deslocamento inteiro do log em relação a UTC.

O modo sem `--detect` permanece compatível com os incrementos anteriores e
continua emitindo os eventos normalizados.

### 10.2 Saída e códigos de processo

Cada alerta é um JSON com tipo de registro, IP, início da janela, instante de
detecção, quantidade de tentativas e usuários observados. O resumo é escrito na
saída de erro, portanto sua ordem visual em relação ao JSON pode variar.

- código `0`: análise concluída sem alertas;
- código `1`: análise concluída com pelo menos um alerta;
- código `2`: erro de leitura, configuração ou ausência de horário normalizado.

O código `1` sinaliza uma descoberta de segurança para facilitar automação; não
representa falha interna da aplicação.

### 10.3 Critérios de aceite

- **CA-16:** sem `--detect`, a saída de eventos e o código zero são preservados.
- **CA-17:** com `--detect`, atingir o limiar gera alerta JSON e código 1.
- **CA-18:** uma análise válida sem atingir o limiar não gera JSON e retorna 0.
- **CA-19:** syslog sem ano no modo de detecção gera mensagem clara e código 2.
- **CA-20:** limiar ou janela inválidos geram código 2.
- **CA-21:** a saída de alerta não contém comandos ou efeitos de bloqueio.

## 11. Quarto incremento — robustez de entrada e saída

### 11.1 Interface e comportamento

- o valor `-` em `log_file` lê o conteúdo da entrada padrão;
- `--utc-offset=±HH:MM` aceita deslocamentos com minutos;
- `--utc-offset-hours` permanece disponível por compatibilidade e é mutuamente
  exclusivo com a nova opção;
- `--alerts-file PATH` grava um alerta JSON por linha e requer `--detect`;
- quando o arquivo de alertas é usado, a saída padrão permanece vazia;
- a entrada continua sendo processada incrementalmente; somente a coleção de
  alertas é mantida até o término para impedir a publicação de resultado parcial
  caso uma inconsistência temporal seja encontrada.

### 11.2 Estratégia para virada do ano

No formato syslog, `--year` define o ano do primeiro evento reconhecido. Como o
log não contém o ano, uma regressão de calendário superior a 180 dias é
interpretada como virada para o ano seguinte. Assim, `Dec 31 23:59:30` seguido de
`Jan 1 00:00:00` é colocado corretamente em anos consecutivos.

A heurística deve ser informada ao usuário porque um arquivo muito esparso ou
fora de ordem pode ser ambíguo. Regressões menores não avançam o ano e continuam
sujeitas à verificação de ordem do detector.

### 11.3 Critérios de aceite

- **CA-22:** usar `-` processa dados da entrada padrão sem fechar o fluxo global.
- **CA-23:** um offset com minutos é aplicado corretamente na conversão para UTC.
- **CA-24:** a opção antiga de fuso em horas permanece funcional.
- **CA-25:** eventos entre dezembro e janeiro recebem anos consecutivos e podem
  participar da mesma janela de detecção.
- **CA-26:** `--alerts-file` grava JSON Lines somente no modo de detecção e não
  duplica os alertas na saída padrão.
- **CA-27:** erros durante leitura, detecção ou escrita retornam código 2.
- **CA-28:** nenhuma dessas opções executa resposta automática ou bloqueio.

## 12. Próximo incremento proposto

Preparar o artefato para entrega e reprodução: adicionar verificação automatizada
em múltiplas versões suportadas do Python, revisar mensagens de erro e ajuda,
documentar limitações de formatos OpenSSH e avaliar o parser com uma amostra
maior e anonimizada. Novos formatos de autenticação só devem ser incluídos após
casos reais e critérios de aceite correspondentes.
