## Plano de Contas Simplificado - ITG 1000

Este módulo implementa o plano de Contas Simplificado baseado na ITG
1000.

O Conselho Federal de Contabilidade aprovou, através da Resolução CFC nº
1.418/2012, a ITG (Interpretação Técnica Geral) 1000, que institui um
Modelo Contábil para as Microempresas e Empresas de Pequeno Porte, para
escrituração contábil simplificada dos seus atos e fatos administrativos

ITG 1000 Permite Adotar modelo contábil para microempresa e empresa de
pequeno porte, inclusive optante do simples nacional.

O Plano de Contas, mesmo que simplificado, deve ser elaborado
considerando-se as especificidades e natureza das operações realizadas,
bem como deve contemplar as necessidades de controle de informações no
que se refere aos aspectos fiscais e gerenciais.

**Na versão 20.0.1.0.0** os grupos de contas (`account.group`) deixaram de
existir no Odoo. As contas sintéticas do plano passaram a ser contas
inativas, ligadas às analíticas pela conta superior (`parent_id`), com o
mesmo código e nome do grupo que substituem. Grupos sem nenhuma conta
analítica abaixo deles não foram mantidos.
