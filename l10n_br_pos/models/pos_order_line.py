# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class PosOrderLine(models.Model):
    _name = "pos.order.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin"]

    # @api.multi
    # def _buscar_produtos_devolvidos(self):
    #     for record in self:
    #         if record.order_id.chave_cfe:
    #             rel_documentos = self.env[
    #                 'l10n_br_account_product.document.related'].search(
    #                 [
    #                     ('access_key', '=', record.order_id.chave_cfe[3:])
    #                 ]
    #             )
    #             qtd_devolvidas = 0
    #             for documento in rel_documentos:
    #                 if documento.invoice_id.state in ('open', 'sefaz_export'):
    #                     for line in documento.invoice_id.invoice_line:
    #                         if record.product_id == line.product_id:
    #                             qtd_devolvidas += line.quantity
    #             record.qtd_produtos_devolvidos = qtd_devolvidas
    #
    # qtd_produtos_devolvidos = fields.Integer(
    #     string="Quantidade devolvida",
    #     compute=_buscar_produtos_devolvidos
    # )
    #
