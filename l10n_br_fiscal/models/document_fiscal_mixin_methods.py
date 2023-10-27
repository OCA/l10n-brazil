# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models

from ..constants.fiscal import COMMENT_TYPE_COMMERCIAL, COMMENT_TYPE_FISCAL


class FiscalDocumentMixinMethods(models.AbstractModel):
    _name = "l10n_br_fiscal.document.mixin.methods"
    _description = "Document Fiscal Mixin Methods"

    def _prepare_br_fiscal_dict(self, default=False):
        self.ensure_one()
        fields = self.env["l10n_br_fiscal.document.mixin"]._fields.keys()

        # we now read the record fiscal fields except the m2m tax:
        vals = self._convert_to_write(self.read(fields)[0])

        # remove id field to avoid conflicts
        vals.pop("id", None)

        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals

    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        return self.mapped("fiscal_line_ids")

    def _get_product_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        fiscal_line_ids = self._get_amount_lines()
        return fiscal_line_ids.filtered(lambda line: line.product_id.type != "service")

    @api.model
    def _get_amount_fields(self):
        """Get all fields with 'amount_' prefix"""
        fields = self.env["l10n_br_fiscal.document.mixin"]._fields.keys()
        amount_fields = [f for f in fields if f.startswith("amount_")]
        return amount_fields

    def _compute_amount(self):
        fields = self._get_amount_fields()
        for doc in self:
            values = {key: 0.0 for key in fields}
            for line in doc._get_amount_lines():
                for field in fields:
                    if field in line._fields.keys():
                        values[field] += line[field]
                    if field.replace("amount_", "") in line._fields.keys():
                        # FIXME this field creates an error in invoice form
                        if field == "amount_financial_discount_value":
                            values[
                                "amount_financial_discount_value"
                            ] += 0  # line.financial_discount_value
                        else:
                            values[field] += line[field.replace("amount_", "")]

            # Valores definidos pelo Total e não pela Linha
            if (
                doc.company_id.delivery_costs == "total"
                or doc.force_compute_delivery_costs_by_total
            ):
                values["amount_freight_value"] = doc.amount_freight_value
                values["amount_insurance_value"] = doc.amount_insurance_value
                values["amount_other_value"] = doc.amount_other_value

            doc.update(values)

    def __document_comment_vals(self):
        return {
            "user": self.env.user,
            "ctx": self._context,
            "doc": self,
        }

    def _document_comment(self):
        for d in self:
            # Fiscal Comments
            d.fiscal_additional_data = d.comment_ids.filtered(
                lambda c: c.comment_type == COMMENT_TYPE_FISCAL
            ).compute_message(
                d.__document_comment_vals(), d.manual_fiscal_additional_data
            )

            # Commercial Comments
            d.customer_additional_data = d.comment_ids.filtered(
                lambda c: c.comment_type == COMMENT_TYPE_COMMERCIAL
            ).compute_message(
                d.__document_comment_vals(), d.manual_customer_additional_data
            )
            d.fiscal_line_ids._document_comment()

    @api.onchange("partner_id")
    def _onchange_partner_id_fiscal(self):
        if self.partner_id:
            self.ind_final = self.partner_id.ind_final
            for line in self._get_amount_lines():
                # reload fiscal data, operation line, cfop, taxes, etc.
                line._onchange_fiscal_operation_id()

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        if self.fiscal_operation_id:
            self.operation_name = self.fiscal_operation_id.name
            self.comment_ids = self.fiscal_operation_id.comment_ids

    def _inverse_amount_freight(self):
        for record in self.filtered(lambda doc: doc._get_product_amount_lines()):
            if (
                record.delivery_costs == "total"
                or record.force_compute_delivery_costs_by_total
            ):
                amount_freight_value = record.amount_freight_value
                if all(record._get_product_amount_lines().mapped("freight_value")):
                    amount_freight_old = sum(
                        record._get_product_amount_lines().mapped("freight_value")
                    )
                    for line in record._get_product_amount_lines()[:-1]:
                        line.freight_value = amount_freight_value * (
                            line.freight_value / amount_freight_old
                        )
                    record._get_product_amount_lines()[
                        -1
                    ].freight_value = amount_freight_value - sum(
                        line.freight_value
                        for line in record._get_product_amount_lines()[:-1]
                    )
                else:
                    amount_total = sum(
                        record._get_product_amount_lines().mapped("price_gross")
                    )
                    for line in record._get_product_amount_lines()[:-1]:
                        if line.price_gross and amount_total:
                            line.freight_value = amount_freight_value * (
                                line.price_gross / amount_total
                            )
                    record._get_product_amount_lines()[
                        -1
                    ].freight_value = amount_freight_value - sum(
                        line.freight_value
                        for line in record._get_product_amount_lines()[:-1]
                    )
                for line in record._get_product_amount_lines():
                    line._onchange_fiscal_taxes()
                record._fields["amount_total"].compute_value(record)
                record.write(
                    {
                        name: value
                        for name, value in record._cache.items()
                        if record._fields[name].compute == "_amount_all"
                        and not record._fields[name].inverse
                    }
                )

    def _inverse_amount_insurance(self):
        for record in self.filtered(lambda doc: doc._get_product_amount_lines()):
            if (
                record.delivery_costs == "total"
                or record.force_compute_delivery_costs_by_total
            ):
                amount_insurance_value = record.amount_insurance_value
                if all(record._get_product_amount_lines().mapped("insurance_value")):
                    amount_insurance_old = sum(
                        record._get_product_amount_lines().mapped("insurance_value")
                    )
                    for line in record._get_product_amount_lines()[:-1]:
                        line.insurance_value = amount_insurance_value * (
                            line.insurance_value / amount_insurance_old
                        )
                    record._get_product_amount_lines()[
                        -1
                    ].insurance_value = amount_insurance_value - sum(
                        line.insurance_value
                        for line in record._get_product_amount_lines()[:-1]
                    )
                else:
                    amount_total = sum(
                        record._get_product_amount_lines().mapped("price_gross")
                    )
                    for line in record._get_product_amount_lines()[:-1]:
                        if line.price_gross and amount_total:
                            line.insurance_value = amount_insurance_value * (
                                line.price_gross / amount_total
                            )
                    record._get_product_amount_lines()[
                        -1
                    ].insurance_value = amount_insurance_value - sum(
                        line.insurance_value
                        for line in record._get_product_amount_lines()[:-1]
                    )
                for line in record._get_product_amount_lines():
                    line._onchange_fiscal_taxes()
                record._fields["amount_total"].compute_value(record)
                record.write(
                    {
                        name: value
                        for name, value in record._cache.items()
                        if record._fields[name].compute == "_amount_all"
                        and not record._fields[name].inverse
                    }
                )

    def _inverse_amount_other(self):
        for record in self.filtered(lambda doc: doc._get_product_amount_lines()):
            if (
                record.delivery_costs == "total"
                or record.force_compute_delivery_costs_by_total
            ):
                amount_other_value = record.amount_other_value
                if all(record._get_product_amount_lines().mapped("other_value")):
                    amount_other_old = sum(
                        record._get_product_amount_lines().mapped("other_value")
                    )
                    for line in record._get_product_amount_lines()[:-1]:
                        line.other_value = amount_other_value * (
                            line.other_value / amount_other_old
                        )
                    record._get_product_amount_lines()[
                        -1
                    ].other_value = amount_other_value - sum(
                        line.other_value
                        for line in record._get_product_amount_lines()[:-1]
                    )
                else:
                    amount_total = sum(
                        record._get_product_amount_lines().mapped("price_gross")
                    )
                    for line in record._get_product_amount_lines()[:-1]:
                        if line.price_gross and amount_total:
                            line.other_value = amount_other_value * (
                                line.price_gross / amount_total
                            )
                    record._get_product_amount_lines()[
                        -1
                    ].other_value = amount_other_value - sum(
                        line.other_value
                        for line in record._get_product_amount_lines()[:-1]
                    )
                for line in record._get_product_amount_lines():
                    line._onchange_fiscal_taxes()
                record._fields["amount_total"].compute_value(record)
                record.write(
                    {
                        name: value
                        for name, value in record._cache.items()
                        if record._fields[name].compute == "_amount_all"
                        and not record._fields[name].inverse
                    }
                )
