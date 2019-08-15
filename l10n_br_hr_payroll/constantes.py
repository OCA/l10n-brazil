# -*- encoding: utf-8 -*-

CATEGORIA_TRABALHADOR = (
    #
    # Empregado e Trabalhador Temporário
    #
    ('101', u'101 - Empregado – Geral, inclusive o empregado público da administração direta ou indireta contratado pela CLT.'),
    ('102', u'102 - Empregado – Trabalhador Rural por Pequeno Prazo da Lei 11.718/2008'),
    ('103', u'103 - Empregado – Aprendiz'),
    ('104', u'104 - Empregado – Doméstico'),
    ('105', u'105 - Empregado – contrato a termo firmado nos termos da Lei 9601/98'),
    ('106', u'106 - Trabalhador Temporário - contrato nos termos da Lei 6.019/74'),
    # ('107', u'107 - Trabalhador não vinculado ao RGPS com direito ao FGTS'),
    ('111', u'106 - Empregado - contrato de trabalho intermitente'),

    #
    # Avulso
    #
    ('201', u'201 - Trabalhador Avulso – Portuário'),
    ('202', u'202 - Trabalhador Avulso – Não Portuário'),
    # ('203', u'203 - Trabalhador Avulso – Não Portuário '
    #         u'(Informação do Contratante)'),

    #
    # Agente público
    #
    ('301', u'301 - Servidor Público Titular de Cargo Efetivo, Magistrado, Ministro de Tribunal de Contas, Conselheiro de Tribunal de Contas e Membro do Ministério Público'),
    ('302', u'302 - Servidor Público – '
            u'Ocupante de Cargo exclusivo em comissão'),
    ('303', u'303 - Agente Político'),
    # ('304', u'304 - Servidor Público – Agente Público'),
    ('305', u'305 - Servidor Público indicado para conselho ou órgão '
            u'deliberativo, na condição de representante do governo, '
            u'órgão ou entidade da administração pública.'),
    ('306', u'401 - Servidor Público Temporário, sujeito a regime '
            u'administrativo especial definido em lei própria'),
    ('307', u'307 - Militar efetivo'),
    ('308', u'308 - Conscrito'),
    ('309', u'309 - Agente Público - Outros'),


    #
    # Cessão
    #
    ('401', u'401 - Dirigente Sindical – Em relação a Remuneração Recebida no'
            u' Sindicato'),
    ('410', u'410 - Trabalhador cedido - informação prestada pelo Cessionário'),


    #
    # Contribuinte Individua
    #
    ('701', u'701 - Contrib. Individual – Autônomo contratado por Empresas em'
            u' geral'),
    # ('702', u'702 - Contrib. Individual – Autônomo contratado por Contrib. '
    #         u'Individual, por pessoa física em geral, ou por missão '
    #         u'diplomática e repartição consular de carreira estrangeiras'),
    # ('703', u'703 - Contrib. Individual – Autônomo contratado por Entidade '
    #         u'Beneficente de Assistência Social isenta da cota patronal'),
    # ('704', u'704 - Excluído.'),
    ('711', u'711 - Contribuinte individual - Transportador autônomo de passageiros'),
    ('712', u'712 - Contribuinte individual - Transportador autônomo de carga'),
    # ('713', u'713 - Contrib. Individual – Transportador autônomo contratado'
    #         u' por Entidade Beneficente de Assistência Social isenta da cota '
    #         u'patronal'),
    ('721', u'721 - Contribuinte individual - Diretor não empregado, com FGTS'),
    ('722', u'722 - Contribuinte individual - Diretor não empregado, sem FGTS'),
    ('723', u'723 - Contribuinte individual - Empresários, sócios e membro de conselho de administração ou fiscal'),
    ('731', u'731 - Contribuinte individual - Cooperado que presta serviços por intermédio de Cooperativa de Trabalho'),
    # ('732', u'732 - Contrib. Individual – Cooperado que presta serviços a '
    #         u'Entidade Beneficente de Assistência Social isenta da cota '
    #         u'patronal ou para pessoa física'),
    # ('733', u'733 - Contrib. Individual – Cooperado eleito para direção da '
    #         u'Cooperativa'),
    ('734', u'734 - Contribuinte individual - Transportador Cooperado que presta serviços por intermédio de cooperativa de trabalho'),
    # ('735', u'735 - Contrib. Individual – Transportador Cooperado que presta'
    #         u' serviços a Entidade Beneficente de Assistência Social isenta '
    #         u'da cota patronal ou para pessoa física'),
    # ('736', u'736 - Contrib. Individual – Transportador Cooperado eleito '
    #         u'para direção da Cooperativa'),
    ('738', u'738 - Contribuinte individual - Cooperado filiado a Cooperativa de Produção'),
    ('741', u'741 - Contribuinte individual - Microempreendedor Individual'),

    ('751', u'751 - Contribuinte individual - Magistrado classista temporário da Justiça do Trabalho ou da Justiça Eleitoral que seja aposentado de qualquer regime previdenciário'),
    ('761', u'761 - Contribuinte individual - Associado eleito para direção de Cooperativa, '
            u'associação ou entidade de classe de qualquer natureza ou finalidade, bem '
            u'como o síndico ou administrador eleito para exercer atividade de direção '
            u'condominial, desde que recebam remuneração'),
    ('771', u'771 - Contribuinte individual - Membro de conselho tutelar, nos termos da Lei no 8.069, de 13 de julho de 1990'),
    ('781', u'781 - Ministro de confissão religiosa ou membro de vida consagrada, de congregação ou de ordem religiosa'),

    #
    # Bolsista
    #
    ('901', u'901 - Estagiário'),
    ('902', u'902 - Médico Residente'),
    ('903', u'903 - Bolsista, nos termos da lei 8958/1994'),
    ('904', u'904 - Participante de curso de formação, como etapa de concurso público, sem vínculo de emprego/estatutário'),
    ('905', u'905 - Atleta não profissional em formação que receba bolsa'),
)
CATEGORIA_TRABALHADOR_DIC = dict(CATEGORIA_TRABALHADOR)

SEFIP_CATEGORIA_TRABALHADOR = {
    '701': '13',
    '702': '13',
    '703': '13',
    '721': '11',
    '722': '11',
    '103': '07'
}

MESES = [
    ('01', u'Janeiro'),
    ('02', u'Fevereiro'),
    ('03', u'Março'),
    ('04', u'Abril'),
    ('05', u'Maio'),
    ('06', u'Junho'),
    ('07', u'Julho'),
    ('08', u'Agosto'),
    ('09', u'Setembro'),
    ('10', u'Outubro'),
    ('11', u'Novembro'),
    ('12', u'Dezembro'),
    ('13', u'13º Salário'),
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
    ('5', u'5-Individualização'),
    ('6', u'6-Individualização - Ação Fiscal'),
    (' ', u'Em branco'),
]
RECOLHIMENTO_GPS = [
    ('1', u'1-GPF no prazo'),
    ('2', u'2-GPF em atraso'),
    ('3', u'3-Não gera GPS'),
]
CENTRALIZADORA = [
    ('0', u'0 - Não centraliza'),
    ('1', u'1 - Centralizadora'),
    ('2', u'2 - Centralizada'),
]


OCORRENCIA_SEFIP = [
    ('01', u'01 - Não exposição a agente nocivo'),
    ('02', u'Exposição a agente nocivo (aposentadoria especial aos '
           u'15 anos de trabalho)'),
    ('03', u'Exposição a agente nocivo (aposentadoria especial aos '
           u'20 anos de trabalho)'),
    ('04', u'Exposição a agente nocivo (aposentadoria especial aos '
           u'25 anos de trabalho)'),
    ('05', u'Mais de um vínculo empregatício (ou fonte pagadora) - '
           u'Não exposição a agente nocivo'),
    ('06', u'Mais de um vínculo empregatício (ou fonte pagadora) - '
           u'Exposição a agente nocivo (aposentadoria especial aos '
           u'15 anos de trabalho)'),
    ('07', u'Mais de um vínculo empregatício (ou fonte pagadora) - '
           u'Exposição a agente nocivo (aposentadoria especial aos '
           u'20 anos de trabalho)'),
    ('08', u'Mais de um vínculo empregatício (ou fonte pagadora) - '
           u'Exposição a agente nocivo (aposentadoria especial aos '
           u'25 anos de trabalho)'),
]


CATEGORIA_TRABALHADOR_SEFIP = [
    ('01', u'01 - Empregado'),
    ('03', u'03 - Trabalhador não vinculado ao RGPS, mas com direito ao FGTS'),
    ('04', u'04 - Empregado sob contrato de trabalho por prazo determinado - '
           u'Lei n° 9.601/98, com as alterações da '
           u'Medida Provisória n° 2.164-41, de 24/08/2001.'),
    ('05', u'05 - Contribuinte individual - Diretor não empregado com FGTS – '
           u'Lei nº 8.036/90, art. 16'),
    ('07', u'07 - Menor aprendiz - Lei n°10.097/2000.'),
    ('11', u'11 - Contribuinte Individual - Diretor não empregado e demais '
           u'empresários sem FGTS.'),
    ('13', u'13 - Contribuinte individual – Trabalhador autônomo ou a este '
           u'equiparado, inclusive o operador de máquina, com contribuição '
           u'sobre remuneração; trabalhador associado à cooperativa de '
           u'produção.'),
    ('21', u'21 - Servidor Público titular de cargo efetivo, magistrado, '
           u'membro do Ministério Público e do Tribunal e Conselho de Contas'),
]

CALCULATED_SPECIFC_RULE = [
    'PENSAO_ALIMENTICIA_PORCENTAGEM',
    'PENSAO_ALIMENTICIA_PORCENTAGEM_FERIAS',
    'PENSAO_ALIMENTICIA_PORCENTAGEM_13',
]

MES_DO_ANO = [
    (1, u'Janeiro'),
    (2, u'Fevereiro'),
    (3, u'Março'),
    (4, u'Abril'),
    (5, u'Maio'),
    (6, u'Junho'),
    (7, u'Julho'),
    (8, u'Agosto'),
    (9, u'Setembro'),
    (10, u'Outubro'),
    (11, u'Novembro'),
    (12, u'Dezembro'),
    (13, u'13º Salário'),
]

MES_DO_ANO2 = [
    (1, u'Janeiro'),
    (2, u'Fevereiro'),
    (3, u'Março'),
    (4, u'Abril'),
    (5, u'Maio'),
    (6, u'Junho'),
    (7, u'Julho'),
    (8, u'Agosto'),
    (9, u'Setembro'),
    (10, u'Outubro'),
    (11, u'Novembro'),
    (12, u'Dezembro'),
]

TIPO_DE_FOLHA = [
    ('normal', u'Folha normal'),
    ('rescisao', u'Rescisão'),
    ('rescisao_complementar', u'Rescisão Complementar'),
    ('ferias', u'Férias'),
    ('decimo_terceiro', u'Décimo terceiro (13º)'),
    ('aviso_previo', u'Aviso Prévio'),
    ('provisao_ferias', u'Provisão de Férias'),
    ('provisao_decimo_terceiro', u'Provisão de Décimo terceiro (13º)'),
    ('licenca_maternidade', u'Licença maternidade'),
    ('auxilio_doenca', u'Auxílio doença'),
    ('auxílio_acidente_trabalho', u'Auxílio acidente de trabalho'),
    ('rpa', u'Recibo de Pagamento a Autonômo'),
]
