# Sistema Web para Elaboracao Automatica de Horarios Escolares

Sistema web para cadastrar dados escolares, montar matriz curricular, gerar horarios automaticamente, validar conflitos e imprimir relatorios.

A versao atual e um sistema funcional, sem dependencias externas, feito com Python puro, HTML, CSS, JavaScript e persistencia principal em SQLite.

## Documentacao

- Documentacao oficial: `DOCUMENTACAO.md`
- Controle das fases: `FASES.md`
- Plano de testes: `TESTES.md`
- Guia de implantacao: `IMPLANTACAO.md`

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

Para liberar acesso na rede interna:

```powershell
iniciar_rede.bat
```

Para criar backup local dos arquivos de dados:

```powershell
backup.bat
```

## Dados

Os dados ficam em:

```text
data/horario.sqlite3
```

A rota de saude da aplicacao fica em:

```text
http://127.0.0.1:8000/api/health
```

## PWA

O sistema pode ser instalado como aplicativo pelo navegador em computadores e celulares compativeis.

Arquivos principais:

```text
static/manifest.webmanifest
static/service-worker.js
static/icons/
```

Observacao: o PWA guarda apenas a interface em cache. Os dados continuam sendo salvos no servidor local em `data/horario.sqlite3`.

## Status

Fases concluidas:

- Fase 1: Base funcional.
- Fase 2: Cadastros completos.
- Fase 3: Regras obrigatorias.
- Fase 4: Gerador automatico robusto.
- Fase 5: Ajuste manual seguro.
- Fase 6: Visualizacoes.
- Fase 7: Relatorios e exportacao.
- Fase 8: Login e seguranca.
- Fase 9: Banco de dados real.
- Fase 10: Interface profissional.
- Fase 11: Testes e validacao.
- Fase 12: Implantacao.

Primeiro acesso:

```text
Usuario: admin
Senha: admin123
```

## Validacao tecnica

```powershell
python -m py_compile app.py
python -m py_compile app.py tests\test_system.py
python -m unittest discover -s tests -v
node --check static\app.js
```
