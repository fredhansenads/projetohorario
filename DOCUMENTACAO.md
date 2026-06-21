# Documentacao oficial do sistema

## 1. Identificacao

Nome do sistema: Sistema Web para Elaboracao Automatica de Horarios Escolares.

Objetivo: apoiar direcao e coordenacao escolar na criacao, validacao, ajuste e impressao de horarios semanais de aulas, reduzindo conflitos entre professores, turmas, salas e cargas horarias.

Versao atual: sistema funcional com Fases 1 a 11 concluidas.

Repositorio: `https://github.com/fredhansenads/projetohorario`

## 2. Situacao atual

O sistema roda localmente usando Python puro, sem dependencias externas. Ele usa um servidor HTTP proprio, frontend em HTML/CSS/JavaScript e persistencia principal em SQLite.

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

Fases planejadas:

- Fase 12: Implantacao.

O roteiro completo esta em `FASES.md`.

## 3. Requisitos para executar

Requisito obrigatorio:

- Python instalado.

Requisitos opcionais para desenvolvimento:

- Node.js, apenas para validar sintaxe do arquivo `static/app.js` com `node --check`.
- Git, para versionamento e envio ao GitHub.

Nao e necessario instalar Django, banco de dados, bibliotecas Python ou pacotes npm na versao atual.

## 4. Como executar

Na pasta do projeto:

```powershell
cd C:\Users\PC-01\Documents\projetohorario\projetohorario
python app.py
```

Depois acesse:

```text
http://127.0.0.1:8000
```

Para usar outra porta:

```powershell
python app.py 8010
```

No Windows, tambem e possivel executar:

```powershell
iniciar.bat
```

Primeiro acesso:

```text
Usuario: admin
Senha: admin123
```

## 5. Estrutura de arquivos

```text
app.py
static/
  index.html
  app.css
  app.js
README.md
FASES.md
DOCUMENTACAO.md
iniciar.bat
data/
  horario.sqlite3
  horario-db.json
```

Descricao:

- `app.py`: servidor, API, persistencia, validacoes e gerador automatico.
- `static/index.html`: estrutura principal da interface.
- `static/app.css`: estilo visual, responsividade e padroes da interface.
- `static/app.js`: logica da interface, buscas, formularios e chamadas para API.
- `README.md`: resumo rapido do projeto.
- `FASES.md`: memoria e roteiro de evolucao da Fase 1 a Fase 12.
- `DOCUMENTACAO.md`: documentacao oficial do sistema.
- `TESTES.md`: plano de testes automatizados e checklist manual.
- `iniciar.bat`: atalho para iniciar o servidor no Windows.
- `data/horario.sqlite3`: banco de dados principal criado automaticamente em tempo de uso.
- `data/horario-db.json`: arquivo legado usado apenas para migracao automatica quando existir.

## 6. Modulos do sistema

### 6.1 Painel

Mostra um resumo do sistema:

- quantidade de professores;
- quantidade de turmas;
- quantidade de aulas geradas;
- pontuacao de qualidade;
- alertas obrigatorios;
- pendencias e preferencias;
- status da base funcional;
- memoria das fases do projeto.

### 6.2 Cadastros

Permite manter os dados basicos da escola:

- escola;
- professores;
- turmas;
- disciplinas;
- salas e ambientes;
- turnos e periodos.

Recursos da interface:

- busca geral por nome, contato, serie, sala e disciplina;
- ordenacao alfabetica das listas;
- contadores por painel;
- estados vazios com orientacao clara.

### 6.3 Matriz curricular

Define a relacao entre:

- turma;
- disciplina;
- professor;
- quantidade de aulas semanais;
- necessidade de aula dupla;
- sala especial;
- restricoes especificas.

A matriz curricular e a principal entrada para a geracao automatica.

A tela possui busca por turma, disciplina, professor e sala, com linhas ordenadas para facilitar conferencia.

### 6.4 Disponibilidade

Permite bloquear ou liberar horarios dos professores por dia e periodo.

A tela possui busca por professor, contato e disciplina, alem de contadores para facilitar revisao em bases maiores.

### 6.5 Grade

Mostra a grade em quatro visoes:

- por turma;
- por professor;
- por sala;
- geral.

Tambem permite inserir, editar e remover aulas manualmente.

Recursos de visualizacao:

- busca por disciplina, professor, turma, sala, dia e periodo;
- listas de selecao ordenadas;
- resumo de conflitos, pendencias e aulas fixadas;
- destaque para aulas fixadas;
- destaque para aulas com conflito;
- indicador de sala especial.

Recursos de ajuste manual seguro:

- selecionar uma aula para mover;
- mover a aula selecionada para um horario livre;
- trocar duas aulas entre si;
- fixar ou desfixar aula;
- validar alteracoes antes de salvar;
- confirmar explicitamente quando a alteracao gera conflito.

### 6.6 Relatorios

Mostra:

- conflitos;
- cargas horarias pendentes;
- grades por turma;
- grades por professor;
- grades por sala;
- resumo de aulas, conflitos e pendencias;
- links de exportacao CSV/TXT por turma, professor, sala e geral;
- exportacao CSV de conflitos e pendencias.

O botao "Imprimir PDF" usa a impressao do navegador para gerar PDF.

## 7. Cadastros disponiveis

### 7.1 Escola

Campos:

- nome da escola;
- endereco;
- ano letivo;
- dias letivos;
- horarios dos periodos.

Formato dos horarios dos periodos:

```text
1a aula; 07:00; 07:50
2a aula; 07:50; 08:40
```

### 7.2 Professores

Campos:

- nome;
- telefone ou e-mail;
- disciplinas que pode lecionar;
- limite de aulas por dia;
- limite de aulas seguidas;
- preferencias de horario;
- disponibilidade por dia e periodo.

### 7.3 Turmas

Campos:

- nome da turma;
- serie/ano;
- turno;
- quantidade de alunos;
- sala padrao;
- dias de aula.

### 7.4 Disciplinas

Campos:

- nome;
- carga semanal padrao;
- se permite aula dupla;
- se exige aula dupla;
- se deve evitar ultimo horario;
- tipo de sala exigido;
- observacoes.

### 7.5 Salas e ambientes

Campos:

- nome;
- capacidade;
- tipo;
- disciplinas compativeis.

Se nenhuma disciplina compativel for informada, a sala aceita todas as disciplinas, salvo restricao da propria disciplina.

### 7.6 Turnos e periodos

Formato de configuracao:

```text
manha; Manha; 1a aula, 2a aula, 3a aula, 4a aula, 5a aula
tarde; Tarde; 1a aula, 2a aula, 3a aula, 4a aula, 5a aula
```

Cada linha representa:

```text
id; nome; periodos separados por virgula
```

## 8. Regras implementadas atualmente

O sistema ja possui validacoes para:

- professor em duas turmas no mesmo horario;
- turma com duas aulas no mesmo periodo;
- sala ocupada por mais de uma turma;
- professor fora da disponibilidade;
- turma recebendo aula fora dos dias configurados;
- sala indisponivel;
- sala incompativel com a disciplina;
- carga horaria semanal incompleta;
- excesso de aulas de uma disciplina no mesmo dia;
- muitas janelas de professor.

As regras obrigatorias foram reforcadas na Fase 3. A tela tambem destaca aulas com conflito e mostra o contexto do problema.

## 9. Geracao automatica

O gerador atual usa multiplas tentativas pontuadas:

1. Preserva aulas fixadas.
2. Ordena a matriz curricular, priorizando itens mais restritivos.
3. Executa varias tentativas com pequena variacao controlada.
4. Tenta alocar aulas respeitando turma, professor, sala, disponibilidade e aula dupla.
5. Mede conflitos, pendencias, alertas, distribuicao e janelas.
6. Escolhe a melhor grade encontrada.
7. Registra mensagens quando nao consegue alocar toda a carga.

O painel mostra a tentativa escolhida, pontuacao, quantidade de aulas fixadas, janelas e penalidade de distribuicao.

## 10. API interna

Rotas principais:

```text
GET    /api/session
POST   /api/login
POST   /api/logout
GET    /api/state
POST   /api/state
GET    /api/users
POST   /api/users
DELETE /api/users?id=<id>
GET    /api/history
GET    /api/backups
POST   /api/backup
GET    /api/health
POST   /api/generate
POST   /api/lesson
DELETE /api/lesson?id=<id>
POST   /api/reset
GET    /api/export
```

Descricao:

- `/api/session`: consulta usuario logado.
- `/api/login`: inicia sessao.
- `/api/logout`: encerra sessao.
- `/api/state`: carrega ou salva o estado completo.
- `/api/users`: lista, cria, atualiza ou remove usuarios.
- `/api/history`: lista historico recente de geracoes.
- `/api/backups`: lista backups manuais.
- `/api/backup`: cria backup manual do estado atual.
- `/api/health`: retorna status da aplicacao.
- `/api/generate`: gera a grade automaticamente.
- `/api/lesson`: insere ou altera uma aula.
- `/api/reset`: restaura dados de exemplo.
- `/api/export`: exporta horarios, conflitos e pendencias em TXT ou CSV.

Parametros de exportacao:

```text
scope=general|class|teacher|room|conflicts|pendencies
id=<id do item, quando scope for class, teacher ou room>
format=txt|csv
```

Exemplos:

```text
/api/export?scope=general&format=csv
/api/export?scope=class&id=<id>&format=txt
/api/export?scope=conflicts&format=csv
```

## 11. Dados e armazenamento

Os dados ficam em:

```text
data/horario.sqlite3
```

O arquivo JSON antigo `data/horario-db.json` e usado apenas como fonte de migracao automatica quando existir.

A pasta `data/` e ignorada pelo Git para evitar salvar dados locais no repositorio.

Para restaurar dados de exemplo, use o botao "Restaurar exemplo" na interface ou chame:

```text
POST /api/reset
```

## 12. Validacao tecnica

Comandos usados para validar a versao atual:

```powershell
python -m py_compile app.py
python -m py_compile app.py tests\test_system.py
python -m unittest discover -s tests -v
node --check static\app.js
```

Teste manual recomendado:

1. Abrir o sistema no navegador.
2. Conferir o painel.
3. Editar um cadastro.
4. Gerar horario.
5. Conferir conflitos e pendencias.
6. Abrir a grade por turma, professor, sala e geral.
7. Abrir relatorios.
8. Testar buscas em cadastros, matriz, disponibilidade e grade.
9. Reduzir a largura da janela e conferir se botoes, tabelas e formularios continuam legiveis.

O checklist completo da coordenacao esta em `TESTES.md`.

## 13. Versionamento

Regra combinada:

- ao concluir cada fase, fazer commit no Git local;
- enviar para o GitHub;
- manter `FASES.md` atualizado.

Commits de referencia:

- `1cb5825`: conclusao da Fase 1.
- `f96cc1e`: conclusao da Fase 2.
- `9d52032`: conclusao da Fase 3.
- `20c4540`: conclusao da Fase 4.
- `09ab8c7`: conclusao da Fase 5.
- `a706582`: conclusao da Fase 6.
- `f4ac667`: conclusao da Fase 7.
- `8c5983d`: conclusao da Fase 8.
- `70a9f58`: conclusao da Fase 9.
- `161edc4`: conclusao da Fase 10.
- A preencher: conclusao da Fase 11.
- `03e8b7b`: roteiro completo das fases.

## 14. Limitacoes conhecidas

- Ainda nao ha PostgreSQL ou banco servidor; a versao atual usa SQLite local.
- A exportacao PDF depende da impressao do navegador.
- A exportacao Excel nativa ainda nao foi implementada; a versao atual oferece CSV.
- A Fase 11 criou testes principais, mas cenarios reais maiores ainda devem ser acompanhados na implantacao.

## 15. Proximas fases

Proxima fase de desenvolvimento: Fase 12 - Implantacao.

Depois dela: manutencao, acompanhamento do uso real e melhorias conforme necessidade da escola.
