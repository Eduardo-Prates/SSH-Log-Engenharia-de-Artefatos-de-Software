# Histórico de versões

As mudanças relevantes do projeto são registradas neste arquivo.

## 0.5.1 — revisão de artefato

- adiciona avaliação crítica pelos quatro critérios de artefatos científicos;
- adiciona protocolo automatizado de reprodução;
- completa metadados de licença e URLs do pacote;
- adiciona orientações de contribuição e citação;
- esclarece instalação, ambiente e limitações no README;
- adiciona ao CI uma verificação das principais alegações do artefato.

## 0.5.0 — qualidade e entrega

- adiciona CI para Python 3.11, 3.12, 3.13 e 3.14;
- adiciona Ruff para lint e formatação;
- adiciona teste sintético de 10.000 linhas;
- documenta arquitetura, limitações e evidências de validação.

## 0.4.0 — robustez operacional

- adiciona entrada padrão, offsets com minutos e arquivo de alertas;
- trata virada de ano em timestamps syslog.

## 0.3.0 — detecção pela CLI

- integra o detector à CLI por `--detect`;
- define limiar, janela, saída JSON e códigos de processo.

## 0.2.0 — detector isolado

- normaliza timestamps para UTC;
- adiciona detector configurável e testes de janela temporal.

## 0.1.0 — parser inicial

- cria estrutura do pacote, parser de `Failed password`, CLI e testes iniciais.

