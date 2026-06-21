# Plano de testes e validacao

Este documento registra a validacao oficial da Fase 11.

## Testes automatizados

Comando principal:

```powershell
python -m unittest discover -s tests -v
```

Comandos complementares:

```powershell
python -m py_compile app.py tests\test_system.py
node --check static\app.js
```

## Cobertura automatizada atual

- Persistencia SQLite em diretorio temporario.
- Carregamento e salvamento do estado.
- Protecao de hashes e salts dos usuarios na resposta publica.
- Login do administrador inicial.
- Criacao de conta para outro usuario e login com a nova conta.
- Bloqueio de senha inicial curta.
- Protecao para manter pelo menos um administrador ativo.
- Geracao completa da grade de exemplo sem conflitos obrigatorios.
- Cenario sem disponibilidade suficiente, com pendencia detectada.
- Conflito de turma no mesmo horario.
- Conflito de sala ocupada no mesmo horario.
- Sala incompativel com disciplina de sala especial.
- Carga horaria incompleta.
- Exportacao CSV da grade.
- API protegida por login.
- Geracao via API com registro no historico.
- Configuracao de implantacao por `HOST`, `PORT` e argumentos de linha de comando.

## Checklist manual da coordenacao

1. Entrar com o usuario administrador.
2. Conferir o painel inicial e a pontuacao.
3. Editar dados da escola.
4. Cadastrar ou editar professor, turma, disciplina e sala.
5. Conferir a matriz curricular.
6. Bloquear um horario de professor na disponibilidade.
7. Gerar o horario.
8. Conferir grade por turma, professor, sala e geral.
9. Buscar uma disciplina ou professor na grade.
10. Inserir uma aula manualmente.
11. Fixar e desfixar uma aula.
12. Mover uma aula para um horario livre.
13. Tentar uma alteracao com conflito e conferir o aviso.
14. Abrir relatorios.
15. Exportar CSV geral, por turma e de conflitos.
16. Usar imprimir PDF pelo navegador.
17. Criar backup manual.
18. Sair e entrar novamente, confirmando que os dados continuam salvos.

## Resultado esperado

- Os testes automatizados devem passar sem falhas.
- A grade de exemplo deve gerar aulas sem conflitos obrigatorios.
- Conflitos manuais devem aparecer de forma clara.
- Relatorios e exportacoes devem abrir sem erro.
- Os dados devem permanecer salvos apos reiniciar o sistema.
