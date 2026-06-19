# Controle das fases do sistema

Este arquivo serve como memoria do projeto. Ele registra o plano completo da Fase 1 ate a Fase 12, o status de cada fase, o que ja foi entregue e o que ainda precisa ser feito.

Regra de trabalho: ao concluir cada fase, salvar no Git local e enviar para o GitHub.

## Fase 1 - Base funcional

Status: concluida.

Objetivo: deixar a aplicacao abrindo no navegador, salvando dados, carregando dados, gerando uma grade inicial e oferecendo um caminho simples para restaurar a base de exemplo.

Entregas concluidas:

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

Criterios de validacao:

- `python -m py_compile app.py`
- `node --check static\app.js`
- `GET /api/health`
- `POST /api/generate`

Commit de conclusao: `1cb5825 Concluir fase 1 do sistema de horarios`.

## Fase 2 - Cadastros completos

Status: concluida.

Objetivo: completar formularios, campos, edicao, remocao e regras basicas dos cadastros de escola, professores, turmas, disciplinas, salas, turnos e periodos.

Entregas concluidas:

- Cadastro da escola com nome, endereco, ano letivo, dias letivos e horarios dos periodos.
- Cadastro de professores com contato, disciplinas habilitadas, limite diario, limite de aulas seguidas e preferencias.
- Cadastro de turmas com serie/ano, turno, quantidade de alunos, sala padrao e dias de aula.
- Cadastro de disciplinas com carga semanal, aula dupla, restricao de ultimo horario, tipo de sala exigido e observacoes.
- Cadastro de salas com capacidade, tipo e disciplinas compativeis.
- Configuracao de turnos e periodos por texto estruturado.
- Normalizacao automatica de disponibilidade quando dias ou periodos mudam.
- Protecao contra remocao de cadastros usados na matriz curricular, turmas ou grade gerada.
- Exibicao resumida dos dados principais nos paineis de cadastro.

Criterios de validacao:

- Formularios principais abrem e salvam.
- Itens em uso nao podem ser removidos sem controle.
- Geracao continua funcionando apos alteracoes nos cadastros.

Commit de conclusao: `f96cc1e Concluir fase 2 de cadastros`.

## Fase 3 - Regras obrigatorias

Status: concluida.

Objetivo: impedir ou sinalizar todos os conflitos obrigatorios do sistema.

Escopo:

- Professor nao pode estar em duas turmas no mesmo horario.
- Turma nao pode ter duas aulas no mesmo periodo.
- Sala nao pode ser usada por duas turmas ao mesmo tempo.
- Professor nao pode ser alocado em horario bloqueado.
- Cada disciplina deve cumprir sua carga horaria semanal.
- Disciplinas que exigem sala especifica devem usar sala correta.
- Aulas duplas obrigatorias devem ficar em periodos consecutivos.
- Turma so pode receber aula nos dias e turnos configurados.
- Professor deve lecionar apenas disciplinas habilitadas para ele, salvo ajuste manual confirmado.
- Sala deve respeitar disponibilidade e compatibilidade.

Criterios de conclusao:

- Validacoes aparecem em lista clara.
- Alteracao manual mostra conflitos imediatamente.
- Gerador automatico evita regras obrigatorias sempre que houver solucao.
- Relatorio de pendencias mostra carga horaria incompleta.

Entregas concluidas:

- Validacao obrigatoria reforcada no backend.
- Conflitos agora incluem contexto da aula: turma, disciplina, professor, dia e periodo.
- Validacao de professor habilitado para disciplina.
- Validacao de aula fora dos dias letivos da escola.
- Validacao de periodo fora do turno configurado para a turma.
- Validacao de sala especial definida na matriz curricular.
- Validacao de correspondencia entre aula e matriz curricular.
- Validacao de aula dupla obrigatoria quebrada.
- Aulas com conflito aparecem destacadas na grade.
- Insercao ou edicao manual retorna conflitos imediatamente.

Commit de conclusao: `9d52032 Concluir fase 3 de regras obrigatorias`.

## Fase 4 - Gerador automatico robusto

Status: concluida.

Objetivo: melhorar o algoritmo de geracao, pontuacao e distribuicao semanal.

Escopo:

- Priorizar disciplinas e professores com mais restricoes.
- Distribuir aulas ao longo da semana.
- Respeitar aula dupla obrigatoria.
- Evitar excesso de uma disciplina no mesmo dia.
- Reduzir janelas dos professores.
- Respeitar preferencias de horario quando possivel.
- Calcular pontuacao de qualidade.
- Registrar mensagens de falha quando a geracao nao conseguir fechar a grade.
- Permitir gerar novamente sem perder aulas fixadas.

Criterios de conclusao:

- Geracao cria grade valida nos dados de exemplo.
- Pontuacao explica a qualidade do horario.
- Falhas sao apresentadas de forma compreensivel.
- Aulas fixadas sao preservadas.

Entregas concluidas:

- Geracao com multiplas tentativas e escolha da melhor pontuacao.
- Preservacao de aulas fixadas antes de gerar novamente.
- Ordenacao de matriz por restricao: aula dupla, sala especial e carga semanal.
- Pontuacao com conflitos, pendencias, alertas, distribuicao e janelas de professores.
- Penalidade para aulas mal distribuidas na semana.
- Penalidade para janelas dos professores.
- Pequena variacao controlada entre tentativas para evitar sempre a mesma grade.
- Resumo da qualidade exibido no painel e nos relatorios.
- Mensagens de falha preservadas quando a geracao nao consegue alocar tudo.

Commit de conclusao: `20c4540 Concluir fase 4 do gerador automatico`.

## Fase 5 - Ajuste manual seguro

Status: concluida.

Objetivo: tornar a edicao manual mais clara, validada e controlada.

Escopo:

- Inserir aula manualmente.
- Editar dia, periodo, professor, sala e disciplina.
- Remover aula.
- Fixar aula para o gerador nao mover.
- Soltar aula fixada.
- Trocar aula entre dois horarios.
- Avisar conflitos antes ou imediatamente apos salvar.
- Destacar celulas com conflito na grade.

Criterios de conclusao:

- Usuario consegue corrigir a grade sem editar JSON.
- Conflitos ficam visiveis no momento do ajuste.
- Aulas fixadas permanecem apos nova geracao.

Entregas concluidas:

- Insercao manual validada no backend antes de salvar.
- Edicao manual validada no backend antes de salvar.
- Confirmacao explicita para salvar alteracoes que geram conflito.
- Botao para fixar e desfixar aulas.
- Aulas fixadas preservadas pelo gerador automatico.
- Selecao de aula para mover para outro horario.
- Troca de horario entre duas aulas selecionadas, com validacao.
- Aulas fixadas e aulas com conflito aparecem destacadas na grade.
- Remocao manual de aula pela interface.

Commit de conclusao: a preencher apos salvar no Git.

## Fase 6 - Visualizacoes

Status: pendente.

Objetivo: consolidar visoes por turma, professor, sala, geral, conflitos e pendencias.

Escopo:

- Grade por turma.
- Grade por professor.
- Grade por sala.
- Grade geral da escola.
- Lista de conflitos.
- Lista de cargas horarias pendentes.
- Resumo da qualidade do horario.
- Filtros e busca nos cadastros e nas grades.
- Indicadores visuais para aulas fixadas, conflitos e salas especiais.

Criterios de conclusao:

- Cada publico consegue consultar seu horario.
- Coordenacao consegue ver a escola inteira.
- Conflitos e pendencias aparecem sem precisar procurar manualmente.

## Fase 7 - Relatorios e exportacao

Status: pendente.

Objetivo: concluir impressao, exportacao e relatorios por publico.

Escopo:

- PDF do horario por turma.
- PDF individual por professor.
- PDF da grade geral.
- Relatorio de conflitos.
- Relatorio de cargas pendentes.
- Exportacao em Excel ou CSV.
- Cabecalho com escola, ano letivo e data de geracao.
- Layout de impressao limpo e legivel.

Criterios de conclusao:

- Relatorios podem ser gerados sem ajuste manual de layout.
- Impressao pelo navegador funciona.
- Exportacao contem dados suficientes para uso externo.

## Fase 8 - Login e seguranca

Status: pendente.

Objetivo: proteger o sistema e separar acesso administrativo.

Escopo:

- Login do administrador.
- Cadastro de usuarios.
- Senhas protegidas.
- Sessao autenticada.
- Controle basico de permissoes.
- Protecao contra alteracoes acidentais.
- Registro de usuario responsavel por geracoes e ajustes.

Criterios de conclusao:

- Sistema nao permite alteracoes sem login.
- Usuario administrador consegue gerenciar acesso.
- Dados sensiveis nao ficam expostos na interface.

## Fase 9 - Banco de dados real

Status: pendente.

Objetivo: substituir ou complementar o JSON por banco de dados adequado para uso continuo.

Escopo:

- Avaliar SQLite para uso local ou PostgreSQL para uso em servidor.
- Criar tabelas definitivas.
- Migrar dados do JSON.
- Manter historico de horarios gerados.
- Permitir multiplos anos letivos.
- Preparar backup e restauracao.

Criterios de conclusao:

- Dados sobrevivem a reinicios e atualizacoes.
- Estrutura suporta crescimento da escola.
- Backup pode ser feito e restaurado.

## Fase 10 - Interface profissional

Status: pendente.

Objetivo: melhorar a experiencia visual e operacional do sistema.

Escopo:

- Melhorar layout dos formularios.
- Criar filtros, buscas e ordenacao.
- Melhorar edicao da grade.
- Adaptar para telas menores.
- Criar estados vazios, mensagens e confirmacoes melhores.
- Padronizar botoes, tabelas e alertas.

Criterios de conclusao:

- Uso diario fica claro para direcao/coordenacao.
- Telas importantes funcionam bem em desktop e notebook.
- Textos, botoes e tabelas nao se sobrepoem.

## Fase 11 - Testes e validacao

Status: pendente.

Objetivo: garantir confiabilidade do sistema antes do uso real.

Escopo:

- Testes de geracao com varios cenarios.
- Testes de conflitos obrigatorios.
- Testes de cadastros incompletos.
- Testes de exportacao.
- Testes de regressao para nao quebrar fases anteriores.
- Checklist manual de uso pela coordenacao.

Criterios de conclusao:

- Principais fluxos passam em teste.
- Erros conhecidos estao documentados ou corrigidos.
- Sistema consegue lidar com dados reais de uma escola pequena.

## Fase 12 - Implantacao

Status: pendente.

Objetivo: deixar o sistema pronto para uso fora do ambiente de desenvolvimento.

Escopo:

- Preparar ambiente final.
- Configurar servidor local, VPS ou hospedagem.
- Definir URL de acesso.
- Criar usuario administrador inicial.
- Configurar backup.
- Documentar uso basico.
- Treinar usuarios.
- Definir rotina de manutencao.

Criterios de conclusao:

- Sistema acessivel no ambiente escolhido.
- Backup definido.
- Usuario principal consegue operar cadastros, geracao, ajustes e relatorios.
