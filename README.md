# Sistema Web para Elaboracao Automatica de Horarios Escolares

Primeira versao funcional de um sistema web para cadastrar dados escolares, montar matriz curricular, gerar horarios automaticamente, validar conflitos e imprimir relatorios.

Esta entrega foi feita sem dependencias externas para rodar imediatamente com Python. A arquitetura deixa o caminho aberto para evoluir depois para Django, PostgreSQL, OR-Tools e geracao de PDF nativa.

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

Os dados ficam em `data/horario-db.json`. A rota `http://127.0.0.1:8000/api/health` mostra o status da aplicacao.

## Controle das fases

O acompanhamento detalhado da conclusao das fases 1 a 7 esta em `FASES.md`.

## Fases de elaboracao

### Fase 1 - Planejamento funcional

O documento original foi transformado em modulos: escola, professores, turmas, disciplinas, salas, turnos, matriz curricular, disponibilidade, geracao automatica, ajustes manuais, validacoes, visualizacoes e relatorios. Tambem foram separadas regras obrigatorias e preferenciais.

### Fase 2 - Estrutura web

Foi criado um servidor HTTP em Python puro (`app.py`), com rotas REST para carregar/salvar estado, gerar horarios, editar aulas e exportar relatorio. A interface fica em `static/index.html`, `static/app.css` e `static/app.js`.

### Fase 3 - Cadastros base

A tela de cadastros permite editar a escola e manter professores, turmas, disciplinas, salas e ambientes. A base inicial vem com dados de exemplo para facilitar testes imediatos.

### Fase 4 - Matriz curricular

A matriz liga turma, disciplina, professor, carga semanal, exigencia de aula dupla e sala especial. Ela e a entrada principal do gerador automatico.

### Fase 5 - Disponibilidade

Cada professor possui uma grade de disponibilidade por dia e periodo. O usuario pode bloquear ou liberar horarios pela interface.

### Fase 6 - Geracao automatica

O gerador usa uma estrategia gulosa: tenta alocar primeiro disciplinas mais restritivas, respeitando turma, professor, sala, disponibilidade, aula dupla e carga horaria semanal. Quando nao consegue alocar tudo, registra pendencias.

### Fase 7 - Validacoes e alertas

O sistema valida conflitos obrigatorios: professor em duas turmas, turma com duas aulas no mesmo periodo, sala duplicada, professor bloqueado, sala indisponivel, sala incompatível e carga horaria incompleta. Tambem emite alertas preferenciais, como excesso de aulas da mesma disciplina no dia e janelas de professor.

### Fase 8 - Ajuste manual e visualizacao

A grade pode ser visualizada por turma, professor, sala e visao geral. O administrador pode inserir, editar, mover ou remover aulas, recebendo alerta quando uma alteracao cria conflito.

### Fase 9 - Relatorios e exportacao

A tela de relatorios mostra conflitos, pendencias e grades por turma. O botao "Imprimir PDF" usa a impressao do navegador para salvar em PDF. Tambem ha exportacao simples em TXT pela rota `/api/export`.

## Proximas evolucoes recomendadas

- Migrar o servidor para Django com autenticacao real.
- Trocar o JSON por PostgreSQL.
- Integrar OR-Tools para otimizacao combinatoria mais forte.
- Gerar PDF com ReportLab ou WeasyPrint.
- Criar visualizacoes especificas por professor, sala e grade geral.
- Adicionar historico de geracoes e bloqueio/fixacao permanente de aulas.
