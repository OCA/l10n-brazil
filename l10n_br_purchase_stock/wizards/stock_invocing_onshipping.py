# @ 2021 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_ISSUER_PARTNER


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

    def _build_invoice_values_from_pickings(self, pickings):
        """
        Build dict to create a new invoice from given pickings
        :param pickings: stock.picking recordset
        :return: dict
        """
        invoice, values = super()._build_invoice_values_from_pickings(pickings)

        purchase_pickings = pickings.filtered(lambda pk: pk.purchase_id)
        if purchase_pickings and self._get_invoice_type() != "in_refund":
            # Case more than one Purchase Order the fields below will be join
            # the others will be overwritting, as done in purchase module,
            # one more field include here Note
            payment_refs = set()
            refs = set()
            # Include Note/Narration
            narration = set()
            for picking in purchase_pickings:
                # Campos informados em qualquer caso
                purchase = picking.purchase_id

                # Campo purchase_id store=false
                # values["purchase_id"] = purchase.id
                if picking.fiscal_operation_id:
                    values["issuer"] = DOCUMENT_ISSUER_PARTNER

                # Refund case don't get values from Purchase Dict
                # TODO: Should get any value?
                purchase_values = purchase._prepare_invoice()

                # Fields to Join
                # origins.add(purchase_values["invoice_origin"])
                payment_refs.add(purchase_values["payment_reference"])
                refs.add(purchase_values["ref"])
                narration.add(purchase_values["narration"])

                # Original dict from purchase module.

                # Fields to get from original dict:
                # - "ref": self.partner_ref or "",
                # - "narration": self.notes,
                # - "currency_id": self.currency_id.id,
                # - "invoice_user_id": self.user_id and self.user_id.id
                #    or self.env.user.id,
                # - "payment_reference": self.partner_ref or "",
                # - "partner_bank_id": partner_bank_id.id,
                # - "invoice_payment_term_id": self.payment_term_id.id,

                # Fields to remove from Original Dict
                vals_to_remove = {
                    "move_type",
                    "partner_id",
                    "fiscal_position_id",
                    "invoice_origin",
                    "invoice_line_ids",
                    "company_id",
                    # Another fields
                    "__last_update",
                    "display_name",
                }

                purchase_values_rm = {
                    k: purchase_values[k] for k in set(purchase_values) - vals_to_remove
                }
                values.update(purchase_values_rm)

            # Fields to join
            if len(purchase_pickings) > 1:
                values.update(
                    {
                        "ref": ", ".join(refs)[:2000],
                        # In this case Origin get Pickings Names
                        # "invoice_origin": ", ".join(origins),
                        "payment_reference": len(payment_refs) == 1
                        and payment_refs.pop()
                        or False,
                        "narration": ", ".join(narration),
                    }
                )

        return invoice, values

    def _get_move_key(self, move):
        """
        Get the key based on the given move
        :param move: stock.move recordset
        :return: key
        """
        key = super()._get_move_key(move)
        if move.purchase_line_id:
            # Field purchase_line_id in account.move is Many2one
            key = key + (move.purchase_line_id,)

        return key

    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        """
        Create invoice line values from given moves
        :param moves: stock.move
        :param invoice: account.invoice
        :return: dict
        """

        values = super()._get_invoice_line_values(moves, invoice_values, invoice)
        # Devido ao KEY com purchase_line_id aqui
        # vem somente um registro
        purchase_moves = moves.filtered(lambda ln: ln.purchase_line_id)
        if purchase_moves:
            purchase_line = purchase_moves.purchase_line_id
            # Campos informados em qualquer caso
            values["purchase_line_id"] = purchase_line.id
            values["analytic_account_id"] = purchase_line.account_analytic_id.id
            values["analytic_tag_ids"] = [(6, 0, purchase_line.analytic_tag_ids.ids)]

            # Refund case don't get values from Purchase Line Dict
            # TODO: Should get any value?
            if self._get_invoice_type() != "in_refund":
                # Same make above, get fields informed in
                # original of Purchase Line dict:
                purchase_line_values = purchase_line._prepare_account_move_line()

                # Fields to get:
                # "display_type": self.display_type,
                # "sequence": self.sequence,

                # Fields to remove:
                vals_to_remove = {
                    "name",
                    "product_id",
                    "product_uom_id",
                    "quantity",
                    "price_unit",
                    "tax_ids",
                    "analytic_account_id",
                    "analytic_tag_ids",
                    "purchase_line_id",
                    # another fields
                    "__last_update",
                    "display_name",
                }

                purchase_line_values_rm = {
                    k: purchase_line_values[k]
                    for k in set(purchase_line_values) - vals_to_remove
                }
                values.update(purchase_line_values_rm)

        return values
