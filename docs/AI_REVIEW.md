# Revisão crítica do artefato por IA

## Identificação

- **Artefato:** SSH Log Sentinel
- **Versão inicialmente avaliada:** 0.5.0
- **Data:** 10/09/2026
- **Ferramenta avaliadora:** OpenAI Codex
- **Critérios solicitados:** disponibilidade, funcionalidade, sustentabilidade e
  reprodutibilidade

Esta revisão usa os [critérios publicados para avaliação de artefatos científicos
do SBSeg 2026](https://doc-artefatos.github.io/sbseg2026/). A classificação
abaixo é uma avaliação crítica, não uma concessão oficial de selos.

## Resumo da avaliação inicial

| Critério | Avaliação inicial | Evidências positivas | Lacunas principais |
| --- | --- | --- | --- |
| Disponibilidade | Parcialmente atendido | Repositório público, README, licença MIT e tag `v0.5.0` acessíveis | Tag leve e mutável como referência sem nova versão de revisão; ausência de metadados de citação e URLs no pacote |
| Funcionalidade | Atendido com ressalvas | Instalação limpa validada, CLI executável, exemplos, 28 testes e CI em quatro versões de Python | Instalação para avaliador não estava consolidada como fluxo principal no README |
| Sustentabilidade | Parcialmente atendido | Código modular, tipos, docstrings, testes, Ruff, CI e arquitetura | Ausência de changelog e guia de contribuição; licença não aparecia nos metadados da distribuição |
| Reprodutibilidade | Parcialmente atendido | Exemplos determinísticos, teste de 10.000 linhas e matriz de CI | Não havia comando único de reprodução; o roteiro anteriormente criado foi removido; faltava mapear alegações a resultados esperados |

## Análise por critério

### Disponibilidade

Uma consulta anônima ao repositório confirmou a branch `main` pública e a tag
`v0.5.0`. README e licença permitem localizar e compreender o artefato. Contudo,
a tag publicada é leve, embora o checklist a descrevesse como anotada, e não há
identificador de arquivamento permanente como DOI.

**Ações:** acrescentar citação, URLs e licença aos metadados; publicar as
correções como 0.5.1 e criar uma nova tag anotada após o CI.

### Funcionalidade

As funcionalidades declaradas podem ser observadas nos exemplos, e os códigos
de saída distinguem ausência de alerta, alerta e erro. A instalação em ambiente
virtual foi validada. A principal lacuna documental era obrigar o avaliador a
reunir instruções dispersas para obter um ambiente limpo.

**Ação:** concentrar requisitos, instalação e exemplo mínimo no README.

### Sustentabilidade

A separação entre parser, normalização, detector e CLI é clara. Testes cobrem
unidades, integração, documentação e volume; Ruff e CI reduzem regressões. A
ausência de histórico de versões e normas de contribuição dificultava evolução
por terceiros.

**Ações:** criar `CHANGELOG.md` e `CONTRIBUTING.md`, além de declarar a licença
MIT nos metadados de empacotamento.

### Reprodutibilidade

Os dados sintéticos são adequados e não carregam riscos de privacidade. O CI
repete a suíte, mas isso não substitui um protocolo que relacione alegações,
comandos e resultados esperados. A remoção do roteiro de demonstração deixou uma
referência histórica sem artefato equivalente na versão publicada.

**Ações:** criar `docs/REPRODUCIBILITY.md`, adicionar `scripts/reproduce.py` e
executar esse protocolo no CI.

## Sugestões não implementadas e justificativas

- **Docker:** não foi adicionado. O pacote usa somente a biblioteca padrão em
  runtime, suporta venv e já é testado em quatro versões; um container aumentaria
  superfície e manutenção sem resolver uma dependência nativa.
- **Bloqueio automático:** rejeitado por segurança e por estar explicitamente
  fora do escopo acadêmico.
- **Novos formatos OpenSSH:** adiados até existirem amostras representativas e
  critérios de aceite, evitando alegar cobertura não validada.
- **DOI ou arquivamento externo:** depende de conta e decisão do autor; permanece
  como recomendação humana para uma entrega formal.
- **Substituição da tag `v0.5.0`:** não realizada porque apagar ou mover uma tag
  pública prejudica consumidores. A correção indicada é publicar `v0.5.1` como
  nova tag anotada.

## Avaliação esperada após as correções

As mudanças elevam funcionalidade, sustentabilidade e reprodutibilidade. A
disponibilidade ficará forte após publicar a versão 0.5.1, confirmar o CI e criar
a tag anotada. Um DOI continua opcional conforme o nível de permanência exigido
pela disciplina.
