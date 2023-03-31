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

    def compute_br_amounts(self):
        # TODO: No account.move do modulo l10n_br_account o metodo
        #  _compute_amount ao chamar o super ao inves de chamar o metodo
        #  acima é chamado apenas o do account.move o que faz com que
        #  os valores Totais fiquem divergentes do calculo que é feito
        #  na localização, a forma encontrada para contornar o problema
        #  é ter esse outro metodo com um nome diferetente.
        #  Reavaliar esse problema na v16 ou versão superior.
        fields = self._get_amount_fields()
        values = {}
        for doc in self:
            values = {key: 0.0 for key in fields}
            lines = doc._get_amount_lines()

            for line in lines:
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

            amount_untaxed = (
                amount_fiscal
            ) = (
                amount_total
            ) = (
                amount_tax
            ) = (
                financial_total
            ) = (
                financial_total_gross
            ) = (
                financial_discount_value
            ) = amount_freight_value = amount_insurance_value = amount_other_value = 0.0

            for line in lines:

                round_curr = line.currency_id or self.env.ref("base.BRL")
                # Valor dos produtos
                price_gross = round_curr.round(line.price_unit * line.quantity)

                amount_untaxed += price_gross - line.discount_value

                amount_fiscal += (
                    round_curr.round(line.fiscal_price * line.fiscal_quantity)
                    - line.discount_value
                )
                amount_tax += line.amount_tax_not_included

                add_to_amount = sum([line[a] for a in line._add_fields_to_amount()])
                rm_to_amount = sum([line[r] for r in line._rm_fields_to_amount()])

                # Valores definidos pelo Total e não pela Linha
                if (
                    doc.company_id.delivery_costs == "total"
                    or doc.force_compute_delivery_costs_by_total
                ):
                    # TODO: Nesse caso os valores do Frete, Seguro e Outros
                    #  estão desatualizados( seria possível atualizar a linha? )
                    #  por isso o valor será somado abaixo
                    add_to_amount = 0.0

                # Valor do documento (NF)
                amount_total += (
                    line.amount_untaxed + line.amount_tax + add_to_amount - rm_to_amount
                )

                # Valor Liquido (TOTAL + IMPOSTOS - RETENÇÕES)
                amount_taxed = (
                    line.amount_untaxed + line.amount_tax + add_to_amount - rm_to_amount
                ) - line.amount_tax_withholding

                # Valor financeiro
                if (
                    line.fiscal_operation_line_id
                    and line.fiscal_operation_line_id.add_to_amount
                    and (not line.cfop_id or line.cfop_id.finance_move)
                ):

                    financial_total += amount_taxed
                    financial_total_gross += amount_taxed + line.discount_value
                    financial_discount_value += line.discount_value
                else:
                    financial_total_gross = financial_total = 0.0
                    financial_discount_value = 0.0

                amount_freight_value += line.freight_value
                amount_insurance_value += line.insurance_value
                amount_other_value += line.other_value

            # Valores definidos pelo Total e não pela Linha
            if (
                doc.company_id.delivery_costs == "total"
                or doc.force_compute_delivery_costs_by_total
            ):
                values["amount_freight_value"] = doc.amount_freight_value
                values["amount_insurance_value"] = doc.amount_insurance_value
                values["amount_other_value"] = doc.amount_other_value

            values.update(
                {
                    "amount_untaxed": amount_untaxed,
                    "amount_total": amount_total,
                    "amount_tax": amount_tax,
                    "amount_price_gross": amount_untaxed,
                    "amount_financial_total": financial_total,
                    "amount_financial_total_gross": financial_total_gross,
                    "amount_freight_value": amount_freight_value,
                    "amount_insurance_value": amount_insurance_value,
                    "amount_other_value": amount_other_value,
                }
            )

        return values

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
    def _onchange_partner_id(self):
        if self.partner_id:
            self.ind_final = self.partner_id.ind_final

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        if self.fiscal_operation_id:
            self.operation_name = self.fiscal_operation_id.name
            self.comment_ids = self.fiscal_operation_id.comment_ids

    def _inverse_amount_freight(self):
        for record in self.filtered(lambda doc: doc._get_amount_lines()):
            if (
                record.delivery_costs == "total"
                or record.force_compute_delivery_costs_by_total
            ):

                amount_freight_value = record.amount_freight_value
                if all(record._get_amount_lines().mapped("freight_value")):
                    amount_freight_old = sum(
                        record._get_amount_lines().mapped("freight_value")
                    )
                    for line in record._get_amount_lines()[:-1]:
                        line.freight_value = amount_freight_value * (
                            line.freight_value / amount_freight_old
                        )
                    record._get_amount_lines()[
                        -1
                    ].freight_value = amount_freight_value - sum(
                        line.freight_value for line in record._get_amount_lines()[:-1]
                    )
                else:
                    amount_total = sum(record._get_amount_lines().mapped("price_gross"))
                    for line in record._get_amount_lines()[:-1]:
                        line.freight_value = amount_freight_value * (
                            line.price_gross / amount_total
                        )
                    record._get_amount_lines()[
                        -1
                    ].freight_value = amount_freight_value - sum(
                        line.freight_value for line in record._get_amount_lines()[:-1]
                    )
                for line in record._get_amount_lines():
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
        for record in self.filtered(lambda doc: doc._get_amount_lines()):
            if (
                record.delivery_costs == "total"
                or record.force_compute_delivery_costs_by_total
            ):

                amount_insurance_value = record.amount_insurance_value
                if all(record._get_amount_lines().mapped("insurance_value")):
                    amount_insurance_old = sum(
                        record._get_amount_lines().mapped("insurance_value")
                    )
                    for line in record._get_amount_lines()[:-1]:
                        line.insurance_value = amount_insurance_value * (
                            line.insurance_value / amount_insurance_old
                        )
                    record._get_amount_lines()[
                        -1
                    ].insurance_value = amount_insurance_value - sum(
                        line.insurance_value for line in record._get_amount_lines()[:-1]
                    )
                else:
                    amount_total = sum(record._get_amount_lines().mapped("price_gross"))
                    for line in record._get_amount_lines()[:-1]:
                        line.insurance_value = amount_insurance_value * (
                            line.price_gross / amount_total
                        )
                    record._get_amount_lines()[
                        -1
                    ].insurance_value = amount_insurance_value - sum(
                        line.insurance_value for line in record._get_amount_lines()[:-1]
                    )
                for line in record._get_amount_lines():
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
        for record in self.filtered(lambda doc: doc._get_amount_lines()):
            if (
                record.delivery_costs == "total"
                or record.force_compute_delivery_costs_by_total
            ):
                amount_other_value = record.amount_other_value
                if all(record._get_amount_lines().mapped("other_value")):
                    amount_other_old = sum(
                        record._get_amount_lines().mapped("other_value")
                    )
                    for line in record._get_amount_lines()[:-1]:
                        line.other_value = amount_other_value * (
                            line.other_value / amount_other_old
                        )
                    record._get_amount_lines()[
                        -1
                    ].other_value = amount_other_value - sum(
                        line.other_value for line in record._get_amount_lines()[:-1]
                    )
                else:
                    amount_total = sum(record._get_amount_lines().mapped("price_gross"))
                    for line in record._get_amount_lines()[:-1]:
                        line.other_value = amount_other_value * (
                            line.price_gross / amount_total
                        )
                    record._get_amount_lines()[
                        -1
                    ].other_value = amount_other_value - sum(
                        line.other_value for line in record._get_amount_lines()[:-1]
                    )
                for line in record._get_amount_lines():
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
