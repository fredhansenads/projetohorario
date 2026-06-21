# Guia de implantacao

Este guia fecha a Fase 12 e descreve como colocar o sistema em uso.

## 1. Ambiente recomendado

Uso local ou rede interna da escola:

- Windows com Python instalado.
- Pasta do projeto em local fixo do computador responsavel.
- Navegador atualizado.
- Backup regular da pasta `data/` ou uso do script `backup.bat`.

Uso em servidor:

- Python instalado.
- Porta HTTP liberada somente para a rede autorizada.
- Processo iniciado com `HOST` e `PORT`.
- Rotina externa de backup do arquivo `data/horario.sqlite3`.

## 2. Execucao local

Na pasta do projeto:

```powershell
python app.py
```

Ou pelo atalho:

```powershell
iniciar.bat
```

URL padrao:

```text
http://127.0.0.1:8000
```

## 3. Execucao em rede interna

Use:

```powershell
iniciar_rede.bat
```

Ou manualmente:

```powershell
$env:HOST="0.0.0.0"
$env:PORT="8000"
python app.py
```

Outros computadores devem acessar pelo IP do computador servidor:

```text
http://IP-DO-COMPUTADOR:8000
```

Antes de usar em rede, confirme regras de firewall e permita acesso somente para pessoas autorizadas.

## 4. Primeiro acesso

Usuario inicial:

```text
Usuario: admin
Senha: admin123
```

Procedimento recomendado apos a primeira entrada:

1. Criar um novo usuario administrador nominal.
2. Criar usuarios de consulta, se necessario.
3. Alterar a senha padrao do administrador inicial ou desativar esse usuario.
4. Registrar quem sera responsavel pelos backups.

## 5. Backup

Backup manual pela interface:

1. Entrar como administrador.
2. Abrir o painel.
3. Usar o botao "Criar backup".

Backup por arquivo:

```powershell
backup.bat
```

O script copia os arquivos encontrados em `data/` para a pasta `backups/` com data e hora no nome.

Arquivo principal:

```text
data/horario.sqlite3
```

Rotina recomendada:

- Backup diario durante o periodo de elaboracao dos horarios.
- Backup antes de grandes alteracoes.
- Copia semanal em local externo ao computador principal.

## 6. Restauracao

Para restaurar um backup de arquivo:

1. Fechar o sistema.
2. Fazer uma copia do arquivo atual `data/horario.sqlite3`.
3. Copiar o backup escolhido para `data/horario.sqlite3`.
4. Iniciar o sistema novamente.
5. Conferir painel, cadastros e grade.

## 7. Verificacao de saude

Com o sistema aberto:

```text
http://127.0.0.1:8000/api/health
```

Em rede, substitua `127.0.0.1` pelo IP do computador servidor.

## 8. Treinamento minimo

Treinar pelo menos uma pessoa da coordenacao para:

- entrar e sair do sistema;
- revisar cadastros;
- atualizar matriz curricular;
- configurar disponibilidade;
- gerar horario;
- ajustar aula manualmente;
- identificar conflitos e pendencias;
- exportar relatorios;
- criar backup;
- executar o checklist de `TESTES.md`.

## 9. Manutencao

Rotina recomendada:

- Executar backup antes de cada rodada importante de geracao.
- Verificar `TESTES.md` antes de atualizacoes.
- Conferir se a pasta `data/` esta sendo preservada.
- Evitar apagar arquivos `.sqlite3`.
- Manter o repositorio atualizado no GitHub apos mudancas do sistema.

## 10. Checklist de aceite

- Sistema abre no computador escolhido.
- Login administrativo funciona.
- Cadastros principais podem ser editados.
- Gerador cria grade.
- Grade abre por turma, professor, sala e geral.
- Relatorios exportam CSV/TXT.
- Backup manual funciona.
- Rota `/api/health` responde.
- Usuario responsavel sabe iniciar, parar e salvar backup.
