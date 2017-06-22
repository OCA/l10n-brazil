# -*- coding: utf-8 -*-
# (c) 2017 KMEE INFORMATICA LTDA - Daniel Sadamo <sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models

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
SEFIP_STATE = [
    ('rascunho',u'Rascunho'),
    ('confirmado',u'Confirmada'),
    ('enviado',u'Enviado'),
]


class L10nBrSefip(models.Model):
    _name = 'l10n_br.hr.sefip'

    state = fields.Selection(selection=SEFIP_STATE, default='rascunho')
    responsible_company_id = fields.Many2one(
        comodel_name='res.company', string=u'Empresa Responsável'
    )
    responsible_user_id = fields.Many2one(
        comodel_name='res.users', string=u'Usuário Responsável'
    )
    company_id = fields.Many2one(comodel_name='res.company', string=u'Empresa')
    mes = fields.Selection(selection=MESES, string=u'Mês')
    ano = fields.Char(string=u'Ano')
    modalidade_arquivo = fields.Selection(
        selection=MODALIDADE_ARQUIVO, string=u'Modalidade do arquivo'
    )
    codigo_recolhimento = fields.Selection(
        string=u'Código de recolhimento', selection=CODIGO_RECOLHIMENTO
    )
    recolhimento_fgts = fields.Selection(
        string=u'Recolhimento do FGTS', selection=RECOLHIMENTO_FGTS
     )
    data_recolhimento_fgts = fields.Date(
        string=u'Data de recolhimento do FGTS'
    )
    codigo_recolhimento_gps = fields.Char(
        string=u'Código de recolhimento do GPS'
    )
    recolhimento_gps = fields.Selection(
        string=u'Recolhimento do GPS', selection=RECOLHIMENTO_GPS
    )
    data_recolhimento_gps = fields.Date(
        string=u'Data de recolhimento do GPS'
    )
    codigo_fpas = fields.Char(string=u'Código FPAS')
    codigo_outras_entidades = fields.Char(string=u'Código de outras entidades')
    centralizadora = fields.Selection(
        selection=CENTRALIZADORA, string=u'Centralizadora'
    )
    data_geracao = fields.Date(string=u'Data do arquivo')
    #Processo ou convenção coletiva
    num_processo = fields.Char(string=u'Número do processo')
    ano_processo = fields.Char(string=u'Ano do processo')
    vara_jcj = fields.Char(string=u'Vara/JCJ')
    data_inicio = fields.Date(string=u'Data de Início')
    data_termino = fields.Date(string=u'Data de término')

    @api.multi
    def gerar_sefip(self):
        for record in self:
