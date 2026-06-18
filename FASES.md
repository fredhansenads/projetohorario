# Controle das fases

Este arquivo acompanha a conclusao das fases 1 a 7 do sistema.

## Fase 1 - Base funcional

Objetivo: deixar a aplicacao abrindo no navegador, salvando dados, carregando dados, gerando uma grade inicial e oferecendo um caminho simples para restaurar a base de exemplo.

Status: concluida.

Entregas:

- Servidor local em Python puro.
- Interface principal com navegacao entre modulos.
- Persistencia em `data/horario-db.json`.
- Dados de exemplo criados automaticamente.
- Botao para gerar horario.
- Botao para salvar alteracoes.
- Botao para restaurar dados de exemplo.
- Rota `/api/health` para conferir se a aplicacao esta saudavel.
- Script `iniciar.bat` para facilitar a execucao no Windows.
- Suporte a porta alternativa com `python app.py 8010`.

Validacao:

- `python -m py_compile app.py`
- `node --check static\app.js`
- `GET /api/health`
- `POST /api/generate`

## Fase 2 - Cadastros completos

Status: pendente.

Meta: completar formularios, campos, edicao, remocao e regras basicas dos cadastros de escola, professores, turmas, disciplinas, salas, turnos e periodos.

## Fase 3 - Regras obrigatorias

Status: pendente.

Meta: impedir ou sinalizar todos os conflitos obrigatorios do sistema.

## Fase 4 - Gerador automatico robusto

Status: pendente.

Meta: melhorar o algoritmo de geracao, pontuacao e distribuicao semanal.

## Fase 5 - Ajuste manual seguro

Status: pendente.

Meta: tornar a edicao manual mais clara, validada e controlada.

## Fase 6 - Visualizacoes

Status: pendente.

Meta: consolidar visoes por turma, professor, sala, geral, conflitos e pendencias.

## Fase 7 - Relatorios

Status: pendente.

Meta: concluir impressao, exportacao e relatorios por publico.
