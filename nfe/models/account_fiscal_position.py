# -*- coding: utf-8 -*-
# Copyright (C) 2016 Trustcode - www.trustcode.com.br
#              Danimar Ribeiro <danimaribeiro@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import api, fields, models, _
from odoo.exceptions import Warning as UserError, except_orm

TOO_MANY_FISCAL_POSITIONS_MSG = _(
    u'''Fiscal Category {fc.name} ({fc!r}) has multiple Fiscal Positions
    ({fp!r}) mapping to CFOP {cfop.code} ({cfop!r}).'''.strip()
)


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    icms_credit = fields.Boolean("Creditar ICMS?")
    ipi_credit = fields.Boolean("Creditar IPI?")
    pis_credit = fields.Boolean("Creditar PIS?")
    cofins_credit = fields.Boolean("Creditar COFINS?")

    def _apply_mapping(self, tax_mapping, inv_line):
        if tax_mapping.tax_code_dest_id:
            inv_line[
                'icms_cst_id'] = tax_mapping.tax_code_dest_id.id
        if tax_mapping.cfop_dest_id:
            inv_line['cfop_id'] = tax_mapping.cfop_dest_id.id
            self._update_fiscal_position(inv_line, tax_mapping.cfop_dest_id)
        if tax_mapping.tax_dest_id:
            line_tax = []
            for tax_line in inv_line['invoice_line_tax_id']:
                tax = self.env['account.tax'].browse(tax_line[1])
                if tax.domain != tax_mapping.tax_dest_id.domain:
                    line_tax.append(tax_line)
                else:
                    line_tax.append((4, tax_mapping.tax_dest_id.id, 0))

            inv_line['invoice_line_tax_id'] = line_tax

    def _update_fiscal_position(self, inv_line, cfop):
        fiscal_category = self.env['l10n_br_account.fiscal.category'].browse(
            inv_line['fiscal_category_id']
        )
        fiscal_position_ids = fiscal_category.fiscal_position_ids.filtered(
            lambda fp: fp.cfop_id == cfop
        )
        try:
            inv_line['fiscal_position'] = (
                fiscal_position_ids.ensure_one() if fiscal_position_ids
                else self
            ).id
        except except_orm:
            raise UserError(TOO_MANY_FISCAL_POSITIONS_MSG.format(
                fc=fiscal_category, fp=fiscal_position_ids, cfop=cfop,
            ))

    @api.multi
    def fiscal_position_map(self, inv_line):
        values = dict(inv_line or {})
        self.ensure_one()
        values['cfop_id'] = self.cfop_id.id
        for tax_mapping in self.tax_ids:
            cfop_src_id_match = (
                tax_mapping.cfop_src_id and
                tax_mapping.cfop_src_id.code == str(values['cfop_xml'])
            )
            tax_src_id_match = (
                tax_mapping.tax_src_id and
                tax_mapping.tax_src_id.id in {
                    j[1] for j in values['invoice_line_tax_id']
                }
            )
            tax_code_src_id_match = (
                tax_mapping.tax_code_src_id.id and
                tax_mapping.tax_code_src_id.id == values['icms_cst_id']
            )

            if cfop_src_id_match and tax_src_id_match \
                    and tax_code_src_id_match:
                self._apply_mapping(tax_mapping, values)
                continue

            if cfop_src_id_match and tax_src_id_match:
                self._apply_mapping(tax_mapping, values)
                continue

            if cfop_src_id_match and tax_code_src_id_match:
                self._apply_mapping(tax_mapping, values)
                continue

            if tax_src_id_match and tax_code_src_id_match:
                self._apply_mapping(tax_mapping, values)
                continue

            if tax_code_src_id_match:
                # A CST de Origem bate então tenta setar CFOP e CST de
                # destino se existir
                self._apply_mapping(tax_mapping, values)
                continue

            if cfop_src_id_match:
                # A CFOP de origem bate então tenta setar CFOP e CST de
                # destino se existir
                self._apply_mapping(tax_mapping, values)

        return values


class AccountFiscalPositionTax(models.Model):
    _inherit = 'account.fiscal.position.tax'

    type = fields.Selection(related='position_id.type', string="Tipo")

    cfop_src_id = fields.Many2one(
        'l10n_br_account_product.cfop',
        string=u"CFOP de Origem",
        help=u"Apenas válido para a importação do xml")
    cfop_dest_id = fields.Many2one(
        'l10n_br_account_product.cfop',
        string=u"CFOP de Destino",
        help=u"Apenas válido para a importação do xml")
