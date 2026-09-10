# Checklist de entrega acadêmica

## Artefato

- [x] Código compatível com Python 3.11 ou superior.
- [x] Instalação limpa em ambiente virtual validada.
- [x] Parser e detector separados da interface CLI.
- [x] Exemplos reproduzíveis e evidências manuais versionados.
- [x] Bloqueio automático mantido fora do escopo.

## Especificação e rastreabilidade

- [x] Requisitos e critérios de aceite registrados em `SPEC.md`.
- [x] Prompts, decisões, refinamentos e validações registrados em `RELATO.txt`.
- [x] Limitações conhecidas declaradas no `README.md` e em `SPEC.md`.
- [x] Arquitetura documentada em `docs/ARCHITECTURE.md`.
- [x] Roteiro de demonstração disponível em `docs/DEMO.md`.

## Qualidade

- [x] Suíte local aprovada em Python 3.14.
- [x] Lint e formatação aprovados pelo Ruff.
- [x] Teste sintético de 10.000 linhas aprovado.
- [x] CI remoto aprovado em Python 3.11, 3.12, 3.13 e 3.14.
- [x] Workflow restrito a permissão de leitura do conteúdo.

## Fechamento pendente

- [x] Executar a suíte após adicionar a documentação final.
- [ ] Revisar o roteiro de demonstração com o aluno.
- [ ] Criar commit final e publicar no GitHub.
- [ ] Confirmar que o CI do commit final está verde.
- [ ] Criar a tag anotada `v0.5.0` e publicá-la.
- [ ] Conferir a renderização do diagrama Mermaid no GitHub.
- [ ] Entregar o link do repositório e as evidências exigidas pela disciplina.

Comandos sugeridos para a tag, somente após todos os itens anteriores:

```powershell
git tag -a v0.5.0 -m "SSH Log Sentinel 0.5.0"
git push origin v0.5.0
```
