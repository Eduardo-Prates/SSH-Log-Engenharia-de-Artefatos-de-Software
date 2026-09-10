# Como contribuir

## Ambiente

Use Python 3.11 ou superior em um ambiente virtual. Instale o projeto e as
ferramentas de desenvolvimento:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Em Linux ou macOS, a ativação equivalente é `source .venv/bin/activate`.

## Verificações obrigatórias

Antes de propor uma mudança, execute:

```powershell
ruff check --no-cache .
ruff format --no-cache --check .
python -m unittest discover -s tests -v
python scripts/reproduce.py
```

## Escopo das mudanças

- preserve a separação entre parser, detector, modelos e CLI;
- acompanhe novos formatos de log com exemplos e critérios de aceite;
- não inclua endereços, usuários ou logs reais sem anonimização;
- não adicione bloqueio automático sem uma nova decisão de escopo e análise de
  segurança;
- atualize `SPEC.md`, `README.md`, testes e `CHANGELOG.md` quando aplicável;
- registre decisões assistidas por IA no `RELATO.txt` sem inventar interações.

