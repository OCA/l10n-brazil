# company_dependent lido com with_company

Campo `company_dependent` é lido com `record.with_company(company).campo`; nunca a
partir do ambiente do usuário quando a empresa do documento pode ser outra.

## Por quê

Sem `with_company`, o valor devolvido é o da empresa do ambiente, não o da empresa do
registro: parâmetro fiscal de uma empresa aplicado ao documento da outra, em silêncio.

# Fonte em inglês; en.po é inerte

String de usuário na fonte (Python, XML, JS) vai em inglês; a tradução pt_BR vai em
`i18n/pt_BR.po`. Não crie nem edite `i18n/en.po` (o pre-commit recusa).

## Por quê

O `msgid` é o texto em inglês da fonte; um `en.po` não traduz nada. Fonte em português
vira termo intraduzível para os outros idiomas e quebra a busca por `msgid`.

# Marcador de schema por subpacote

Em módulo `*_spec` e nos que estendem `spec_driven_model`, o marcador `_spec_schema`
fica no subpacote dos modelos daquele schema; não estenda modelo de outro schema dentro
do pacote marcado.

## Por quê

O carregamento do spec usa o marcador para resolver a hierarquia de classes; um modelo
de outro schema no mesmo pacote derruba o registro inteiro na inicialização, não só o
módulo.

# Registro principal escolhido, não o primeiro do recordset

Quando um documento guarda vários anexos ou respostas (XML enviado, resposta,
`procEvento`), o "principal" é guardado em campo próprio ou escolhido por nome, nunca
`anexos[0]`.

## Por quê

`ir.attachment` ordena por id decrescente e um recordset acumulado não preserva ordem de
criação: o "primeiro" muda conforme o caminho que criou os registros.

# Dado montado por script passa pelos onchanges

Empresa, parceiro, produto e documento fiscal criados por script, hook ou teste usam
`Form` (ou chamam os onchanges) em vez de `create` com dicionário cru.

## Por quê

Sem onchange a empresa fica sem os impostos padrão e o pedido sem operação fiscal; o
teste passa e a base "montada" não emite. Campo `related` herdado também vence o
`compute` quando o valor vem cru.

## Exceções

Teste unitário que fixa explicitamente todos os campos fiscais necessários.
