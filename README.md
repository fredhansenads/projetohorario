# Sistema Web para Elaboracao Automatica de Horarios Escolares

Sistema web para cadastrar dados escolares, montar matriz curricular, gerar horarios automaticamente, validar conflitos e imprimir relatorios.

A versao atual e um MVP funcional, sem dependencias externas, feito com Python puro, HTML, CSS, JavaScript e persistencia em JSON.

## Documentacao

- Documentacao oficial: `DOCUMENTACAO.md`
- Controle das fases: `FASES.md`

## Como executar

```powershell
python app.py
```

Para usar outra porta:

```powershell
python app.py 8010
```

Depois acesse:

```text
http://127.0.0.1:8000
```

No Windows, tambem e possivel dar dois cliques em `iniciar.bat`.

## Dados

Os dados ficam em:

```text
data/horario-db.json
```

A rota de saude da aplicacao fica em:

```text
http://127.0.0.1:8000/api/health
```

## Status

Fases concluidas:

- Fase 1: Base funcional.
- Fase 2: Cadastros completos.
- Fase 3: Regras obrigatorias.
- Fase 4: Gerador automatico robusto.
- Fase 5: Ajuste manual seguro.

Proxima fase:

- Fase 6: Visualizacoes.

## Validacao tecnica

```powershell
python -m py_compile app.py
node --check static\app.js
```
