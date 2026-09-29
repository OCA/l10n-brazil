## 20.0.2.2.1 (2026)

O Odoo 20.0 removeu o campo `company_type` dos parceiros e o modelo
`res.bank` (e com ele o diretório de bancos):

- `is_company` passou a ser calculado a partir do campo `vat`, que continua
  armazenando tanto o CPF (pessoa física) quanto o CNPJ (pessoa jurídica) sem
  formatação;
- o código do banco (COMPE) agora é informado diretamente na conta bancária
  (`res.partner.bank.code_bc`), no lugar de vir do modelo `res.bank`.

## 12.0.1.0.0 (2019)

A partir da versão 12.0 foi extraído o pacote de validações cadastrais
`erpbrasil.base` no intuito de minimizar o código que depende de uma
versão especifica do Odoo e para desenvolver sinergias com outras
comunidades de código aberto.

## 11.0 (unreleased)

Devido ao atraso com a versão 11.0 foi decido de pular a versão 11.0 e
trabalhar direitamente para a versão 12.0.

## 10.0.1.0.0 (2017)

Devido ao trabalho enorme com a reescritura do módulo de contabilidade
na versão 9 e a problemas pessoas de um dos autores, essa versão atrasou
um pouco para sair.

## 9.0.1.0.0 (2015)

## 8.0.1.0.0 (2014)

## 7.0.1.0.0 (2013)

Mudança do Launchpad para Github. Mudança importante com a unificação
das tabelas de parceiros e endereços.

## 6.1.1.0.0 (2012)

## 6.0.1.0.0 (2011)

## 5.0.1.0.0 (2009)

Este módulo foi criado na versão 5.0 do Odoo então chamado OpenERP. Era
inicialmente hospedado na plataforma Launchpad.
