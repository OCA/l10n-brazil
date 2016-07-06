# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp

SIMPLIFIED_INVOICE_TYPE = [
    ('nfce', u'NFC-E'),
    ('sat', u'SAT'),
    ('paf', u'PAF-ECF'),
]

PRINTER = [
    ('epson-tm-t20', u'Epson TM-T20'),
    ('bematech-mp4200th', u'Bematech MP4200TH'),
    ('daruma-dr700', u'Daruma DR700'),
    ('elgin-i9', u'Elgin I9'),
]


class PosConfig(models.Model):
    _inherit = 'pos.config'

    simplified_invoice_limit = fields.Float(
        string=u'Simplified invoice limit',
        digits=dp.get_precision('Account'),
        help=u'Over this amount is not legally posible to create a '
             u'simplified invoice',
        default=3000)
    simplified_invoice_type = fields.Selection(
        string=u'Simplified Invoice Type',
        selection=SIMPLIFIED_INVOICE_TYPE,
        help=u'Tipo de documento emitido pelo PDV',
    )

    save_identity_automatic = fields.Boolean(
        string=u'Save new client identity automatic',
        default=True
    )

    iface_sat_via_proxy = fields.Boolean(
        string=u'SAT',
        help=u"Ao utilizar o SAT é necessário ativar esta opção"
    )

    cnpj_homologacao = fields.Char(
        string=u'CNPJ homologação',
        size=18
    )

    ie_homologacao = fields.Char(
        string=u'IE homologação',
        size=16
    )

    cnpj_software_house = fields.Char(
        string=u'CNPJ software house',
        size=18
    )

    sat_ambiente = fields.Selection(
        string=u'Ambiente SAT',
        related='company_id.ambiente_sat',
        store=True
    )

    sat_path = fields.Char(
        string=u'SAT path'
    )

    numero_caixa = fields.Integer(
        string=u'Número do Caixa',
        copy=False
    )

    cod_ativacao = fields.Char(
        string=u'Código de ativação',
    )

    impressora = fields.Selection(
        selection=PRINTER,
        string=u'Impressora',
    )

    printer_params = fields.Char(
        string=u'Printer parameters'
    )

    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Fiscal Category'
    )


    @api.multi
    def retornar_dados(self):
        if self.ambiente_sat == 'homologacao':
            return (self.cnpj_fabricante,
                    self.ie_fabricante,
                    self.cnpj_software_house)
        else:
            return (self.company_id.cnpj_cpf,
                    self.company_id.inscr_est,
                    self.cnpj_software_house or
                    self.company_id.cnpj_software_house)
