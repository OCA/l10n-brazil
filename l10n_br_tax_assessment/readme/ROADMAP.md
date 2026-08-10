- Dedução, retenção na fonte e débito especial abatem o valor a
  recolher, mas não geram partida no lançamento de encerramento: a
  contrapartida de cada um é uma conta própria, que o
  `account.tax.group` do core não modela.
- O bloco M da EFD Contribuições ainda não lê desta apuração, porque o
  módulo da EFD Contribuições não está mesclado na série.
- A classificação de débito e crédito usa `type_tax_use` do imposto.
  Imposto usado nos dois sentidos precisaria de um critério mais fino.
- Consolidação de PJ multi-estabelecimento: a EFD Contribuições é
  entregue pela pessoa jurídica, centralizada na matriz. Somar as
  apurações de PIS e COFINS das filiais (companies) numa apuração
  central é um épico próprio; esta versão apura por company.
