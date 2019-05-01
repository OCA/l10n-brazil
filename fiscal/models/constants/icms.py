# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

ICMS_ORIGIN = (
    ('0', '0 - Nacional, exceto as indicadas nos códigos 3, 4, 5 e 8'),
    ('1', '1 - Estrangeira – importação direta, exceto a indicada no '
          'código 6'),
    ('2', '2 – Estrangeira – adquirida no mercado interno, exceto a indicada '
         'no código 7'),
    ('3', '3 – Nacional – mercadoria ou bem com Conteúdo de Importação '
         'superior a 40% (quarenta por cento) e inferior ou igual a '
         '70% (setenta por cento)'),
    ('4', '4 – Nacional – cuja produção tenha sido feita em conformidade com '
         'os processos produtivos básicos de que tratam o Decreto-lei '
         'n° 288/67 e as Leis (federais) nos 8.428/91, 8.397/91, '
         '10.176/2001 e 11.484/2007'),
    ('5', '5 – Nacional – mercadoria ou bem com Conteúdo de Importação '
         'inferior ou igual a 40% (quarenta por cento)'),
    ('6', '6 – Estrangeira – importação direta, sem similar nacional, '
         'constante em lista de Resolução CAMEX e gás natural'),
    ('7', '7 – Estrangeira – adquirida no mercado interno, sem similar '
         'nacional, constante em lista de Resolução CAMEX e gás natural'),
    ('8', '8 – Nacional – mercadoria ou bem com Conteúdo de Importação '
         'superior a 70% (setenta por cento). (cf. Ajuste SINIEF 15/2013)'))


ICMS_BASE_TYPE = [
    ('0', u'Margem Valor Agregado (%)'),
    ('1', u'Pauta (valor)'),
    ('2', u'Preço Tabelado Máximo (valor)'),
    ('3', u'Valor da Operação')]


ICMS_BASE_TYPE_DEFAULT = '0'


ICMS_ST_BASE_TYPE = [
    ('0', u'Preço tabelado ou máximo  sugerido'),
    ('1', u'Lista Negativa (valor)'),
    ('2', u'Lista Positiva (valor)'),
    ('3', u'Lista Neutra (valor)'),
    ('4', 'Margem Valor Agregado (%)'),
    ('5', 'Pauta (valor)')]


ICMS_ST_BASE_TYPE_DEFAULT = '4'
