# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = "res.company"

    ambiente_sat = fields.Selection(
        selection=[
            ('homologacao', 'Homologação'),
            ('producao', 'Produção'),
        ],
        string='Ambiente SAT',
        # required=True,
        default='homologacao'
    )
    cnpj_software_house = fields.Char(
        string='CNPJ software house',
        size=18
    )
    sign_software_house = fields.Text(
        string="Assinatura da Software House",
    )
    out_pos_fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Pos Out Fiscal Operation',
        # domain="[('journal_type','=','sale'), ('state', '=', 'approved'),"
        # " ('fiscal_type','=','product'), ('type','=','output')]"
        )
    refund_pos_fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Pos Refund Fiscal Operation',
        # domain="[('journal_type','=','sale_refund'),"
        # "('state', '=', 'approved'), ('fiscal_type','=','product'),"
        # " ('type','=','input')]"
    )
