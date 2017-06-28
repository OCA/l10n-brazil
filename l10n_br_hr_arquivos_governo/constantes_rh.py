# -*- encoding: utf-8 -*-

CATEGORIA_TRABALHADOR = (
    ('101', u'101 - Empregado – Geral'),
    ('102', u'102 - Empregado – Trabalhador Rural por Pequeno Prazo da Lei '
            u'11.718/2008'),
    ('103', u'103 - Empregado – Aprendiz'),
    ('104', u'104 - Empregado – Doméstico'),
    ('105', u'105 - Empregado – contrato a termo firmado nos termos da'
            u' Lei 9601/98'),
    ('106', u'106 - Empregado – contrato por prazo determinado nos termos da '
            u'Lei 6019/74'),
    ('107', u'107 - Trabalhador não vinculado ao RGPS com direito ao FGTS'),
    ('201', u'201 - Trabalhador Avulso – Portuário'),
    ('202', u'202 - Trabalhador Avulso – Não Portuário '
            u'(Informação do Sindicato)'),
    ('203', u'203 - Trabalhador Avulso – Não Portuário '
            u'(Informação do Contratante)'),
    ('301', u'301 - Servidor Público – Titular de Cargo Efetivo'),
    ('302', u'302 - Servidor Público – '
            u'Ocupante de Cargo exclusivo em comissão'),
    ('303', u'303 - Servidor Público – Exercente de Mandato Eletivo'),
    ('304', u'304 - Servidor Público – Agente Público'),
    ('305', u'305 - Servidor Público vinculado a RPPS indicado para conselho '
            u'ou órgão representativo, na condição de representante do govern'
            u'o, órgão ou entidade da administração pública'),
    ('401', u'401 - Dirigente Sindical – Em relação a Remuneração Recebida no'
            u' Sindicato'),
    ('701', u'701 - Contrib. Individual – Autônomo contratado por Empresas em'
            u' geral'),
    ('702', u'702 - Contrib. Individual – Autônomo contratado por Contrib. '
            u'Individual, por pessoa física em geral, ou por missão '
            u'diplomática e repartição consular de carreira estrangeiras'),
    ('703', u'703 - Contrib. Individual – Autônomo contratado por Entidade '
            u'Beneficente de Assistência Social isenta da cota patronal'),
    ('704', u'704 - Excluído.'),
    ('711', u'711 - Contrib. Individual – Transportador autônomo contratado'
            u' por Empresas em geral'),
    ('712', u'712 - Contrib. Individual – Transportador autônomo contratado'
            u' por Contrib. Individual, por pessoa física em geral, ou por mis'
            u'são diplomática e repartição consular de carreira estrangeiras'),
    ('713', u'713 - Contrib. Individual – Transportador autônomo contratado'
            u' por Entidade Beneficente de Assistência Social isenta da cota '
            u'patronal'),
    ('721', u'721 - Contrib. Individual – Diretor não empregado com FGTS'),
    ('722', u'722 - Contrib. Individual – Diretor não empregado sem FGTS'),
    ('731', u'731 - Contrib. Individual – Cooperado que presta serviços a '
            u'empresa por intermédio de cooperativa de trabalho'),
    ('732', u'732 - Contrib. Individual – Cooperado que presta serviços a '
            u'Entidade Beneficente de Assistência Social isenta da cota '
            u'patronal ou para pessoa física'),
    ('733', u'733 - Contrib. Individual – Cooperado eleito para direção da '
            u'Cooperativa'),
    ('734', u'734 - Contrib. Individual – Transportador Cooperado que presta'
            u' serviços a empresa por intermédio de cooperativa de trabalho'),
    ('735', u'735 - Contrib. Individual – Transportador Cooperado que presta'
            u' serviços a Entidade Beneficente de Assistência Social isenta '
            u'da cota patronal ou para pessoa física'),
    ('736', u'736 - Contrib. Individual – Transportador Cooperado eleito '
            u'para direção da Cooperativa'),
    ('741', u'741 - Contrib. Individual – Cooperado filiado a cooperativa '
            u'de produção'),
    ('751', u'751 - Contrib. Individual – Micro Empreendedor Individual, '
            u'quando contratado por PJ'),
    ('901', u'901 - Estagiário'),
)
CATEGORIA_TRABALHADOR_DIC = dict(CATEGORIA_TRABALHADOR)

SEFIP_CATEGORIA_TRABALHADOR = {
    '701':'13',
    '702':'13',
    '703':'13',
    '721':'11',
    '722':'11',
    '103':'07'
}

MESES = [
    ('1',u'Janeiro'),
    ('2',u'Fevereiro'),
    ('3',u'Março'),
    ('4',u'Abril'),
    ('5',u'Maio'),
    ('6',u'Junho'),
    ('7',u'Julho'),
    ('8',u'Agosto'),
    ('9',u'Setembro'),
    ('10',u'Outubro'),
    ('11',u'NOvembro'),
    ('12',u'Dezembro'),
    ('13',u'Décimo Terceiro'),
]

MODALIDADE_ARQUIVO = [
    (' ', u'Recolhimento ao FGTS e Declaração à Previdência'),
    ('1', u'Declaração ao FGTS e à Previdência'),
    ('9', u'Confirmação Informações anteriores – Rec/Decl ao FGTS e'
          u' Decl à Previdência'),
]

CODIGO_RECOLHIMENTO = [
    ('115', u'115 - Recolhimento ao FGTS e informações à Previdência Social'),
    ('130', u'130 - Recolhimento ao FGTS e informações à Previdência Social '
            u'relativas ao trabalhador avulso portuário'),
    ('135', u'135 - Recolhimento e/ou declaração ao FGTS e informações à '
            u'Previdência Social relativas ao trabalhador avulso não '
            u'portuário'),
    ('145', u'145 - Recolhimento ao FGTS  de diferenças apuradas pela CAIXA'),
    ('150', u'150 - Recolhimento ao FGTS  e informações à Previdência Social '
            u'de empresa prestadora de serviços com cessão de mâo-de-obra e '
            u'empresa de trabalho temporário Lei nº 6.019/74, em relação aos '
            u'empregados cedidos, ou de obra de construção civil '
            u'- empreitada parcial'),
    ('155', u'155 - Recolhimento ao FGTS  e informações à Previdência Social '
            u'de obra de construção civil - empreitada total ou obra própria'),
    ('211', u'211 - Declaração para a Previdência Social de Cooperativa de '
            u'Trabalho relativa aos contribuintes individuais cooperados que '
            u'prestam serviçõs a tomadores'),
    ('307', u'307 - Recolhimento de Parcelamento de débito com o FGTS'),
    ('317', u'317 - Recolhimento de Parcelamento de débito com o FGTS de '
            u'empresa com tomador de serviços'),
    ('327', u'327 - Recolhimento de Parcelamento de débito com o FGTS '
            u'priorizando os valores devidos aos trabalhores'),
    ('337', u'337 - Recolhimento de Parcelamento de débito com o FGTS de '
            u'empresas com tomador de serviços, priorizando os valores devidos'
            u' aos trabalhadores'),
    ('345', u'345 - Recolhimento de parcelamento de débito com o FGTS relativo'
            u' a diferença de recolhimento, priorizando os valores devidos '
            u'aos trabalhadores'),
    ('418', u'418 - Recolhimento recursal para o FGTS'),
    ('604', u'604 - Recolhimento ao FGTS  de entidades com fins filantrópicos '
            u'- Decreto-Lei nº194, de 24/02/1967 (competências anteriores '
            u'a 10/1989'),
    ('608', u'608 - Recolhimento ao FGTS e informações à Previdência Social '
            u'relativo a dirigente sindical'),
    ('640', u'640 - Recolhimento ao FGTS para empregado não optante '
            u'(competência anterior a 10/1988)'),
    ('650', u'650 - Recolhimento ao FGTS e Informações à Previdência Social'
            u' relativo a Anistiados, Reclamatória Trabalhista, Reclamatória '
            u'Trabalhista com reconhecimento de vínculo, Acordo ou Dissídio '
            u'ou Convenção Coletiva, Comissão Conciliação Prévia ou Núcleo'
            u' Intersindical Conciliação Trabalhista'),
    ('660', u'660 - Recolhimento exclusivo ao FGTS relativo a Anistiados,'
            u' Conversão Licença Saúde em Acidente Trabalho, Reclamatória '
            u'Trabalhista, Acordo ou Dissídio ou Convenção Coletiva, '
            u'Comissão Conciliação Prévia ou Núcleo Intersindical '
            u'Conciliação Trabalhista'),
]
RECOLHIMENTO_FGTS = [
    ('1', u'1-GRF no prazo'),
    ('2', u'2-GRF em atraso'),
    ('3', u'3-GRF em atraso - Ação Fiscal'),
]
RECOLHIMENTO_GPS = [
    ('1', u'1-GPF no prazo'),
    ('2', u'2-GPF em atraso'),
    ('3', u'3-GPF em atraso - Ação Fiscal'),
]
CENTRALIZADORA = [
    ('0', u'0 - Não centraliza'),
    ('1', u'1 - Centralizadora'),
    ('2', u'2 - Centralizada'),
]
