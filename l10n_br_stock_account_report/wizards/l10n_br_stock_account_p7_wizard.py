# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

import pytz

from odoo import _, api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import PRODUCT_FISCAL_TYPE


class L10nBRP7ModelInventoryReportWizard(models.TransientModel):
    _name = "l10n_br.p7.model.inventory.report.wizard"
    _description = "Brazilian P7 Model Inventory Report Wizard"

    compute_at_date = fields.Selection(
        selection=[(0, _("Current Inventory")), (1, _("At a Specific Date"))],
        string="Compute",
        help="Choose to analyze the current inventory or from"
        " a specific date in the past.",
    )

    date = fields.Datetime(
        string="Inventory at Date",
        help="Choose a date to get the inventory at that date",
        default=fields.Datetime.now,
    )

    def print_report(self):

        data = self.read()[0]
        result = self.get_report_values()
        data.update(
            {
                "language": self.env.user.lang,
                "lines": result["lines"],
                "header": result["header"],
                "total": result["total"],
                "total_product_types": result["total_product_types"],
                "footer": result["footer"],
            }
        )

        return self.env.ref(
            "l10n_br_stock_account_report.l10n_br_p7_model_inventory_report"
        ).report_action(self, data=data)

    @api.model
    def get_report_values(self):

        # Informar no relatorio o fuso/horario do usuario
        if self.env.context.get("tz"):
            time_zone = pytz.timezone(self.env.context.get("tz"))
        else:
            time_zone = pytz.utc
        to_date_with_tz = pytz.utc.localize(self.date, "%Y-%m-%d %H:%M:%S").astimezone(
            time_zone
        )

        header, footer = self.header_footer(to_date_with_tz, time_zone)
        lines, total, total_product_types = self.lines()

        result = {
            "lines": lines,
            "header": header,
            "total": total,
            "total_product_types": total_product_types,
            "footer": footer,
        }

        return result

    def header_footer(self, to_date_with_tz, time_zone):

        company = self.env.user.company_id
        header = {
            "company_name": company.name,
            "cnpj": company.cnpj_cpf,
            "inscr_est": company.inscr_est,
            "date": to_date_with_tz.strftime("%d/%m/%Y"),
        }

        footer = {
            "date_generate": datetime.now(tz=time_zone).strftime("%d/%m/%Y %H:%M:%S"),
            "user_name": self.env.user.name,
        }

        return header, footer

    def lines(self):

        # Precision
        obj_precision = self.env["decimal.precision"]
        account_precision = obj_precision.precision_get("Account")
        price_precision = obj_precision.precision_get("Product Price")

        # TODO: Teria outra forma de fazer isso na v12 ?
        # Format Lang
        fmt = "%f" if account_precision is None else "%.{precision}f"
        lang_code = self.env.user.lang or "pt_BR"
        obj_lang = self.env["res.lang"].search([("code", "=", lang_code)])

        # Apenas produto com NCM e com Quantidades
        # maiores que zero devem ser considerados
        products = (
            self.env["product.product"]
            .with_context(
                to_date=self.date,
                default_compute_at_date=self.env.context["default_compute_at_date"],
            )
            .search([("ncm_id", "!=", False), ("qty_available", ">", 0.0)])
        )

        # Ordena a lista pelo NCM
        products_sorted_by_ncm = sorted(products, key=lambda p: p.ncm_id.code)

        result_lines = []
        tmp_total_value_ncm = tmp_total_value = 0.0
        tmp_ncm_controler = None
        fiscal_type_dict = {}

        for product in products_sorted_by_ncm:

            tmp_ncm_controler_line = False

            price_used = product.get_history_price(
                self.env.user.company_id.id,
                date=self.date,
            )

            # TODO: ainda é necessário fazer essa validação decimal
            decimal = product.qty_available - int(product.qty_available)
            if decimal:
                qty_precision = account_precision
            else:
                qty_precision = 0

            # Valor de Inventario do Produto
            product_inventory_value = product.qty_available * price_used

            # Calcula o Total por NCM
            tmp_total_value_ncm += round(product_inventory_value, account_precision)

            if product.ncm_id.code != tmp_ncm_controler:
                tmp_ncm_controler = product.ncm_id.code
                tmp_total_value_ncm = round(product_inventory_value, account_precision)
                # A validação abaixo é necessária p/
                # não preencher a primeira linha
                if type(tmp_ncm_controler) != bool:
                    tmp_ncm_controler_line = True

            result_lines.append(
                {
                    "product_name": product.name or "",
                    "product_code": product.default_code or "",
                    "product_uom": product.uom_id.name,
                    "product_qty": obj_lang.format(
                        fmt.format(precision=qty_precision),
                        product.qty_available,
                        True,
                        True,
                    ),
                    "price_unit": obj_lang.format(
                        fmt.format(precision=price_precision),
                        round(price_used, price_precision),
                        True,
                        True,
                    ),
                    "partial_total_value": obj_lang.format(
                        fmt.format(precision=account_precision),
                        round(product_inventory_value, account_precision),
                        True,
                        True,
                    ),
                    "ncm": product.ncm_id.code,
                    "total_value_ncm": obj_lang.format(
                        fmt.format(precision=account_precision),
                        tmp_total_value_ncm,
                        True,
                        True,
                    ),
                    "ncm_controller": tmp_ncm_controler_line,
                }
            )

            # Calcula o Valor Total do Inventário
            tmp_total_value += product_inventory_value

            # Calcula os valores Totais por Tipo Fiscal

            # PRODUCT_FISCAL_TYPE = (
            #     ("00", "Mercadoria para Revenda"),
            #     ("01", "Matéria-prima"),
            #     ("02", "Embalagem"),
            #     ("03", "Produto em Processo"),
            #     ("04", "Produto Acabado"),
            #     ("05", "Subproduto"),
            #     ("06", "Produto Intermediário"),
            #     ("07", "Material de Uso e Consumo"),
            #     ("08", "Ativo Imobilizado"),
            #     ("09", "Serviços"),
            #     ("10", "Outros insumos"),
            #     ("99", "Outras"),
            # )
            for fiscal_type in PRODUCT_FISCAL_TYPE:
                if fiscal_type[0] == product.product_tmpl_id.fiscal_type:
                    if not fiscal_type_dict.get(fiscal_type[1]):
                        fiscal_type_dict[fiscal_type[1]] = product_inventory_value
                    else:
                        fiscal_type_dict[fiscal_type[1]] = (
                            fiscal_type_dict[fiscal_type[1]] + product_inventory_value
                        )

        # Organiza o resultado do Valor Total por Tipo Fiscal
        result_product_types = []
        list_fiscal_type = list(fiscal_type_dict.keys())
        # A lista precisa ser ordenada para não
        # variar entre os relatorios impressos
        list_fiscal_type.sort()
        for fiscal_type_name in list_fiscal_type:
            result_product_types.append(
                {
                    "name": fiscal_type_name,
                    "value": obj_lang.format(
                        fmt.format(precision=account_precision),
                        fiscal_type_dict.get(fiscal_type_name),
                        True,
                        True,
                    ),
                }
            )

        # Valor Total do Inventário
        total = {
            "total": obj_lang.format(
                fmt.format(precision=account_precision), tmp_total_value, True, True
            )
        }

        return result_lines, total, result_product_types
