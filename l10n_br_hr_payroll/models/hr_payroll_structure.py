# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import fields, models

TIPO_SAQUE = (
    ('01', u'01 - Sem justa causa (incl. indireta)'),
    ('02', u'02 - Por culpa recíproca ou força maior'),
    ('03', u'03 - Extinção total da empresa'),
    ('04', u'04 - Extinção do contrato por prazo determinado'),
    ('  ', u'Código mov. H, J e M'),
    ('23', u'23 - Por falecimento'),
)

TIPO_DESLIGAMENTO_RAIS = (
    ('10', u'10 - Rescisão de contrato de trabalho por justa causa e '
           u'iniciativa do empregador ou demissão de servidor'),
    ('11', u'11 - Rescisão de contrato de trabalho sem justa causa por '
           u'iniciativa do empregador ou exoneração de oficio de servidor de '
           u'cargo efetivo ou exoneração de cargo em comissão'),
    ('12', u'12 - Término do contrato de trabalho'),
    ('20', u'20 - Rescisão com justa causa por iniciativa do empregado ('
           u'rescisão indireta)'),
    ('21', u'21 - Rescisão sem justa causa por iniciativa do empregado ou '
           u'exoneração de cargo efetivo a pedido do servidor'),
    ('22', u'22 - Posse em outro cargo inacumulável (específico para servidor '
           u'público)'),
    ('30', u'30 - Transferência de empregado entre estabelecimentos da mesma '
           u'empresa ou para outra empresa, com ônus para a cedente'),
    ('31', u'31 - Transferência de empregado entre estabelecimentos da mesma '
           u'empresa ou para outra empresa, sem ônus para a cedente'),
    ('32', u'32 - Readaptação (específico para servidor público)'),
    ('33', u'33 - Cessão'),
    ('34', u'34 - Redistribuição (específico para servidor público)'),
    ('40', u'40 - Mudança de regime trabalhista'),
    ('50', u'50 - Reforma de militar para a reserva remunerada'),
    ('60', u'60 - Falecimento'),
    ('62', u'62 - Falecimento decorrente de acidente do trabalho típico (que '
           u'ocorre no exercício de atividades profissionais a serviço da '
           u'empresa)'),
    ('63', u'63 - Falecimento decorrente de acidente do trabalho de trajeto ('
           u'ocorrido no trajeto residência–trabalho–residência)'),
    ('64', u'64 - Falecimento decorrente de doença profissional'),
    ('70', u'70 - Aposentadoria por tempo de contribuição, com rescisão '
           u'contratual'),
    ('71', u'71 - Aposentadoria por tempo de contribuição, sem rescisão '
           u'contratual'),
    ('72', u'72 - Aposentadoria por idade, com rescisão contratual'),
    ('73', u'73 - Aposentadoria por invalidez, decorrente de acidente do '
           u'trabalho'),
    ('74', u'74 - Aposentadoria por invalidez, decorrente de doença '
           u'profissional'),
    ('75', u'75 - Aposentadoria compulsória'),
    ('76', u'76 - Aposentadoria por invalidez, exceto a decorrente de doença '
           u'profissional ou acidente do trabalho'),
    ('78', u'78 - Aposentadoria por idade, sem rescisão contratual'),
    ('79', u'79 - Aposentadoria especial, com rescisão contratual'),
    ('80', u'80 - Aposentadoria especial, sem rescisão contratual'),
)

TIPO_AFASTAMENTO_SEFIP = (
    ('H', u'H - Rescisão, com justa causa, por iniciativa do empregador.'),
    ('I1', u'I1 - Rescisão, sem justa causa, por iniciativa do empregador.'),
    ('I2', u'I2 - Rescisão por culpa recíproca ou força maior.'),
    ('I3', u'I3 - Rescisão por término do contrato a termo.'),
    ('I4', u'I4 - Rescisão, sem justa causa, do contrato de trabalho do '
           u'empregado doméstico, por iniciativa do empregador .'),
    ('J', u'J - Rescisão do contrato de trabalho por iniciativa do '
          u'empregado.'),
    ('K', u'K - Rescisão a pedido do empregado ou por iniciativa do '
          u'empregador, com justa causa, no caso de empregado não optante, '
          u'com menos de um ano de serviço.'),
    ('L', u'L - Outros motivos de rescisão do contrato de trabalho.'),
    ('M', u'M - Mudança de regime estatutário.'),
    ('N1', u'N1 - Transferência do empregado para outro estabelecimento da '
           u'mesma empresa.'),
    ('N2', u'N2 - Transferência do empregado para outra empresa que tenha '
           u'assumido os encargos trabalhistas, sem que tenha havido rescisão '
           u'de contrato de trabalho.'),
    ('N3', u'N3 - Empregado proveniente de transferência de outro '
           u'estabelecimento da mesma empresa ou de outra empresa, '
           u'sem rescisão do contrato de trabalho.'),
    ('O1', u'O1 - Afastamento temporário por motivo de acidente do trabalho, '
           u'por período superior a 15 dias.'),
    ('O2', u'O2 - Novo afastamento temporário em decorrência do mesmo '
           u'acidente do trabalho.'),
    ('O3', u'O3 - Afastamento temporário por motivo de acidente do trabalho, '
           u'por período igual ou inferior a 15 dias.'),
    ('P1', u'P1 - Afastamento temporário por motivo de doença, por período '
           u'superior a 15 dias.'),
    ('P2', u'P2 - Novo afastamento temporário em decorrência da mesma doença, '
           u'dentro de 60 dias contados da cessação do afastamento anterior.'),
    ('P3', u'P3 - Afastamento temporário por motivo de doença, por período '
           u'igual ou inferior a 15 dias.'),
    ('Q1', u'Q1 - Afastamento temporário por motivo de licença-maternidade ('
           u'120 dias).'),
    ('Q2', u'Q2 - Prorrogação do afastamento temporário por motivo de '
           u'licença-maternidade.'),
    ('Q3', u'Q3 - Afastamento temporário por motivo de aborto não criminoso.'),
    ('Q4', u'Q4 - Afastamento temporário por motivo de licença-maternidade '
           u'decorrente de adoção ou guarda judicial de criança até (um) ano '
           u'de idade (120 dias).'),
    ('Q5', u'Q5 - Afastamento temporário por motivo de licença-maternidade '
           u'decorrente de adoção ou guarda judicial de criança a partir de '
           u'1(um) ano até 4(quatro) anos de idade (60 dias).'),
    ('Q6', u'Q6 - Afastamento temporário por motivo de licença-maternidade '
           u'decorrente de adoção ou guarda judicial de criança de 4 (quatro) '
           u'até 8 (oito) anos de idade (30 dias).'),
    ('R', u'R - Afastamento temporário para prestar serviço militar.'),
    ('S2', u'S2 - Falecimento.'),
    ('S3', u'S3 - Falecimento motivado por acidente do trabalho.'),
    ('U1', u'U1 - Aposentadoria.'),
    ('U3', u'U3 - Aposentadoria por invalidez.'),
    ('V3', u'V3 - Remuneração de comissão e/ou percentagens devidas após a '
           u'extinção de contrato de trabalho.'),
    ('W', u'W - Afastamento temporário para exercício de mandato sindical.'),
    ('X', u'X - Licença sem vencimentos.'),
    ('Y', u'Y - Outros motivos de afastamento temporário.'),
    ('Z1', u'Z1 - Retorno de afastamento temporário por motivo de '
           u'licença-maternidade'),
    ('Z2', u'Z2 - Retorno de afastamento temporário por motivo de acidente do '
           u'trabalho'),
    ('Z3', u'Z3 - Retorno de novo afastamento temporário em decorrência do '
           u'mesmo acidente do trabalho.'),
    ('Z4', u'Z4 - Retorno de afastamento temporário por motivo de prestação '
           u'de serviço militar.'),
    ('Z5', u'Z5 - Outros retornos de afastamento temporário e/ou licença.'),
    ('Z6', u'Z6 - Retorno de afastamento temporário por motivo de acidente do '
           u'trabalho, por período igual ou inferior a 15 dias.'),
)

TIPO_AFASTAMENTO_CEF = (
    ('CR0', u'CR0  -Rescisão culpa recíproca.'),
    ('FE1', u'FE1 - Rescisão do contrato de trabalho por falecimento do '
            u'empregador individual por opção do empregado.'),
    ('FE2', u'FE2 - Rescisão do contrato de trabalho por falecimento do '
            u'empregador individual sem continuidade da atividade da '
            u'empresa.'),
    ('FM0', u'FM0 - Rescisão por força maior.'),
    ('FT1', u'FT1 - Rescisão do contrato de trabalho por falecimento do '
            u'empregado.'),
    ('JC2', u'JC2 - Despedida por justa causa pelo empregador.'),
    ('PD0', u'PD0 - Extinção normal do contrato de trabalho por prazo '
            u'determinado.'),
    ('RA1', u'RA1 - Rescisão antecipada, pelo empregado, do contrato de '
            u'trabalho por prazo determinado.'),
    ('RA2', u'RA2 - Rescisão antecipada, pelo empregador do contrato de '
            u'trabalho por prazo determinado.'),
    ('RI2', u'RI2 - Rescisão Indireta.'),
    ('SJ1', u'SJ1 - Rescisão contratual a pedido do empregado.'),
    ('SJ2', u'SJ2 - Rescisão contratual sem justa causa, pelo empregador.'),
)


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    tipo_estrutura = fields.Selection(
        selection=[
            ('normal', u'Folha Normal'),
            ('ferias', u'Férias'),
            ('adiantamento_13', u'Adiantamento do 13º'),
            ('segunda_parcela_13', u'Segunda Parcela do 13º'),
            ('rescisao', u'Rescisão'),
            ('rescisao_complementar', u'Rescisão Complementar'),
            ('base', u'Base')
        ],
        string=u'Tipo de Estrutura de Salários',
        required=True,
        default='base'
    )

    estrutura_ferias_id = fields.Many2one(
        'hr.payroll.structure',
        u'Estrutura de Férias',
        domain="[('tipo_estrutura','=','ferias')]"
    )

    estrutura_adiantamento_13_id = fields.Many2one(
        'hr.payroll.structure',
        u'Estrutura de 13º Salário - Adiantamento',
        domain="[('tipo_estrutura','=','adiantamento_13')]"
    )

    estrutura_13_id = fields.Many2one(
        'hr.payroll.structure',
        u'Estrutura de 13º Salário',
        domain="[('tipo_estrutura','=','segunda_parcela_13')]"
    )

    # Aba de rescisão
    afastamento_imediato = fields.Boolean(
        string=u'Afastamento imediato na rescisão (justa causa, término de '
               u'contrato, etc.):',
    )

    dispensado_empregador = fields.Boolean(
        string=u'Dispensa pelo empregador:',
    )

    tipo_afastamento_sefip = fields.Selection(
        selection=TIPO_AFASTAMENTO_SEFIP,
        string=u'Código do afastamento ou movimentação no SEFIP:',
    )

    tipo_afastamento_cef = fields.Selection(
        selection=TIPO_AFASTAMENTO_CEF,
        string=u'Código do afastamento ou movimentação na C.E.F.:',
    )

    tipo_saque = fields.Selection(
        selection=TIPO_SAQUE,
        string=u'Código de saque:',
    )

    tipo_desligamento_rais = fields.Selection(
        selection=TIPO_DESLIGAMENTO_RAIS,
        string=u'Código desligamento RAIS:',
    )

    children_ids = fields.One2many(
        copy=False
    )
