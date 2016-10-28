# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class ResCompany(models.Model):
    _inherit = "res.company"

    ambiente_sat = fields.Selection(
        [
            ('homologacao', u'Homologação'),
            ('producao', u'Produção'),
        ],
        string='Ambiente SAT',
        required=True,
        default='homologacao'
    )
    cnpj_software_house = fields.Char(
        string=u'CNPJ software house',
        size=18
    )
    sign_software_house = fields.Text(
        string=u"Assinatura da Software House",
    )
    out_pos_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        'Categoria Fiscal de Padrão de Saida do PDV',
        domain="[('journal_type','=','sale'), ('state', '=', 'approved'),"
        " ('fiscal_type','=','product'), ('type','=','output')]")
    refund_pos_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        string='Categoria Fiscal de Devolução do PDV',
        domain="[('journal_type','=','sale_refund'),"
        "('state', '=', 'approved'), ('fiscal_type','=','product'),"
        " ('type','=','input')]"
    )
