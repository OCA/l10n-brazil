# Sem bump de versão no manifest

Não altere `version` no `__manifest__.py` em PR de correção ou melhoria. O bot da OCA
faz o bump ao mesclar, conforme o comando de merge do mantenedor.

## Exceções

Migração para série nova (a versão muda com a série) e módulo novo.

# README gerado só em módulo novo

Em módulo existente, edite só `readme/*.md`; não commite `README.rst` nem
`static/description/index.html` regenerados (o bot regenera ao mesclar). Em módulo novo,
commite os três, senão o pylint da OCA reprova o módulo sem README.

# Dependência externa pelo nome do pacote

`external_dependencies` lista nomes de módulo Python importáveis
(`"python": ["erpbrasil.base"]`), nunca especificador de versão
(`"erpbrasil.base>=2.4.3"`). Versão mínima vai em `requirements.txt` do repositório,
gerado pelo pre-commit a partir dos manifests.

## Por quê

Especificador no manifest vira `ModuleNotFoundError` no CI, porque o Odoo tenta importar
a string inteira. A pista é a linha duplicada no `requirements.txt` gerado.

# Commit com IA leva Assisted-by

Todo commit com assistência de ferramenta de IA termina com o trailer
`Assisted-by: <nome da ferramenta>`. Nunca `Co-authored-by` para IA.

## Por quê

É a política de IA da OCA: autoria é humana, assistência é declarada. O trailer é
legível por máquina e não polui a lista de contribuidores.

## Exceções

Commit sem nenhuma assistência de IA não leva o trailer; não reescrever commits antigos
para acrescentá-lo.

# Série no título do PR, nunca no commit

Título do PR: `[20.0][FIX] l10n_br_nfe: o que muda`. Título do commit:
`[FIX] l10n_br_nfe: o que muda`, sem a série.

## Por quê

O commit é portado para outras séries pelo `oca-port` e o título vai junto; a série no
commit vira mentira na branch seguinte.

# Confirmar que a API existe nesta série

Antes de usar `self.env._`, `/list`, `_compute_terms()["line_ids"]`, `<list>` ou
qualquer API lembrada de outra série, confirme com `git grep` no código desta branch
(core e addons). Se não existir, use a forma desta série.

## Por quê

Sintaxe da série nova em branch antiga passa no CI (o atributo simplesmente não é lido,
a tradução não acontece, a view não casa) e entrega uma feature inerte com check verde.

# Comentário explica o código, não a conversa

Comentário diz o que não é óbvio no código (por que, não o quê), em uma ou duas linhas.
O raciocínio, as alternativas e o contexto da mudança vão no corpo do PR.

## Por quê

Blocos de comentário narrando a decisão são o sinal mais visível de texto gerado e os
mantenedores pedem remoção. O PR guarda a conversa; o código guarda a regra.

# Texto público sem detalhe interno

PR, issue, comentário e commit não citam cliente, volume de dados, hardware nem branch
de fork que o revisor não conhece. Diga "em base de produção com muitos documentos", não
o nome e o número.

## Por quê

O repositório é público e permanente; o revisor precisa do fato (reproduzível), não da
origem. Branch interna citada confunde quem revisa e não existe para quem lê depois.
