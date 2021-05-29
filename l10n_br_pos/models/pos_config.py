# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

SIMPLIFIED_INVOICE_TYPE = [
    ('nfce', 'NFC-E'),
    ('sat', 'SAT'),
    ('paf', 'PAF-ECF'),
]

PRINTER = [
    ('epson-tm-t20', 'Epson TM-T20'),
    ('bematech-mp4200th', 'Bematech MP4200TH'),
    ('daruma-dr700', 'Daruma DR700'),
    ('elgin-i9', 'Elgin I9'),
]


class PosConfig(models.Model):
    _inherit = 'pos.config'

    @api.model
    def _default_out_pos_fiscal_operation_id(self):
        return self.company_id.out_pos_fiscal_operation_id

    @api.model
    def _default_refund_pos_fiscal_operation_id(self):
        return self.company_id.refund_pos_fiscal_operation_id

    # @api.multi
    # @api.constrains('lim_data_alteracao')
    # def _check_lim_data_alteracao(self):
    #     if self.lim_data_alteracao < 0:
    #         raise ValidationError("Somente números positivos são válidos")

    simplified_invoice_limit = fields.Float(
        string='Simplified invoice limit',
        digits=dp.get_precision('Account'),
        help='Over this amount is not legally posible to create a simplified invoice',
        default=3000)

    simplified_invoice_type = fields.Selection(
        string='Simplified Invoice Type',
        selection=SIMPLIFIED_INVOICE_TYPE,
        help='Tipo de documento emitido pelo PDV',
    )

    save_identity_automatic = fields.Boolean(
        string='Save new client',
        help='Activating will save the customer identity automatic',
        default=True
    )

    lim_data_alteracao = fields.Integer(
        string="Atualizar dados (meses)",
        default=3,
    )

    crm_ativo = fields.Boolean(
        string='CRM ativo?',
        default=False,
    )

    cpf_nota = fields.Boolean(
        string='Inserir CPF na nota',
        default=False
    )

    iface_sat_via_proxy = fields.Boolean(
        string='SAT',
        help="Ao utilizar o SAT é necessário ativar esta opção"
    )

    cnpj_homologacao = fields.Char(
        string='CNPJ homologação',
        size=18
    )

    ie_homologacao = fields.Char(
        string='IE homologação',
        size=16
    )

    cnpj_software_house = fields.Char(
        string='CNPJ software house',
        size=18
    )

    sat_ambiente = fields.Selection(
        string='Ambiente SAT',
        related='company_id.ambiente_sat',
        store=True
    )

    sat_path = fields.Char(
        string='SAT path'
    )

    numero_caixa = fields.Integer(
        string='Número do Caixa',
        copy=False
    )

    cod_ativacao = fields.Char(
        string='Código de ativação',
    )

    impressora = fields.Selection(
        selection=PRINTER,
        string='Impressora',
    )

    printer_params = fields.Char(
        string='Printer parameters'
    )

    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Fiscal Operation'
    )
    
    out_pos_fiscal_operation_id = fields.Many2one(
        'l10n_br_fiscal.operation',
        'Categoria Fiscal de Padrão de Saida do PDV',
        # domain="[('journal_type','=','sale'), ('state', '=', 'approved'),"
        # " ('fiscal_type','=','product'), ('type','=','output')]",
        default=_default_out_pos_fiscal_operation_id,
    )
    refund_pos_fiscal_operation_id = fields.Many2one(
        'l10n_br_fiscal.operation',
        string='Categoria Fiscal de Devolução do PDV',
        # domain="[('journal_type','=','sale_refund'),"
        # "('state', '=', 'approved'), ('fiscal_type','=','product'),"
        # " ('type','=','input')]",
        default=_default_refund_pos_fiscal_operation_id,
    )

    assinatura_sat = fields.Char(
        'Assinatura no CFe'
    )

    enviar_pedido_cupom_fiscal = fields.Boolean(
        string='Enviar pedido no cupom fiscal'
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
