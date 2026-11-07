Transporte da CBS da apuração assistida, consumindo as APIs assíncronas
publicadas pela Receita Federal em setembro de 2026.

Implementa os hooks deixados em aberto pelo `l10n_br_assisted_assessment`:

- abre as solicitações de débitos e créditos em `apuracao-cbs/v2`, usando a
  raiz de 8 dígitos do CNPJ, porque a apuração é consolidada por contribuinte
  e não por estabelecimento;
- expõe o endpoint de callback informado como `urlRetorno`, respondendo à
  validação `HEAD` que o gateway faz antes de aceitar a solicitação e
  guardando a URL pré-assinada de download que chega depois;
- consulta o endpoint de status como caminho de recuperação, porque o
  callback nem sempre é entregue;
- baixa e interpreta o arquivo devolvido, encaminhando o conteúdo ao período
  certo. Uma única resposta traz o período corrente e ajustes de períodos
  anteriores, e só o que mudou desde a consulta anterior, então as linhas são
  mescladas e não substituídas.

O IBS é servido pelo CGIBS com endpoints próprios e fica fora do escopo deste
addon.
