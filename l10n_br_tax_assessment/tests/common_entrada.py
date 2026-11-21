# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

import logging
import re
from datetime import date, datetime

from odoo.tests.common import Form

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon

_logger = logging.getLogger(__name__)


class SpedEntradaCommon(AccountMoveBRCommon):
    """Company, supplier and supplier invoice for the tests of the entry books.

    It lives here, the common ancestor of the assessment and of both SPED
    modules, so the tests of the EFD ICMS/IPI and of the EFD Contribuicoes
    build the same entry. The document is created straight in
    ``l10n_br_fiscal.document``, the way the NF-e import leaves it: issued by
    the partner, ``imported_document`` set and the taxes of the file on the lines.
    """

    # "presumed" (cumulative PIS/COFINS) or "real" (non-cumulative)
    profit_calculation = "presumed"

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        if company_name == "company_1_data":
            company_name = "empresa 1 entrada"
        else:
            company_name = "empresa 2 entrada"
        chart_template = cls.env.ref("l10n_br_coa_generic.l10n_br_coa_generic_template")
        piscofins = (
            "tax_pis_cofins_nao_columativo"
            if cls.profit_calculation == "real"
            else "tax_pis_cofins_columativo"
        )
        res = super().setup_company_data(
            company_name,
            chart_template,
            tax_framework="3",
            is_industry=True,
            industry_type="00",
            profit_calculation=cls.profit_calculation,
            ripi=True,
            piscofins_id=cls.env.ref(f"l10n_br_fiscal.{piscofins}").id,
            icms_regulation_id=cls.env.ref("l10n_br_fiscal.tax_icms_regulation").id,
            cnae_main_id=cls.env.ref("l10n_br_fiscal.cnae_3101200").id,
            document_type_id=cls.env.ref("l10n_br_fiscal.document_55").id,
            **kwargs,
        )
        res["company"].partner_id.state_id = cls.env.ref("base.state_br_sp").id
        chart_template.load_fiscal_taxes()
        return res

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()
        cls.company = cls.company_data["company"]
        if cls.profit_calculation == "real":
            cls._use_the_non_cumulative_rates()
        # the supplier of the tests is a taxpayer of the normal regime: a supplier
        # of the Simples Nacional passes no ICMS credit on (LC 123/2006, art. 23)
        cls.partner_a.fiscal_profile_id = cls.env.ref(
            "l10n_br_fiscal.partner_fiscal_profile_cnt"
        )
        cls._doc_number = 100

    @classmethod
    def _use_the_non_cumulative_rates(cls):
        """configure_normal_company_taxes (the common of l10n_br_account, shared
        by the tests of other modules) defines the cumulative PIS 0.65% and
        COFINS 3%. A company of the non-cumulative regime pays the basic rates
        1.65% and 7.6%, so the definitions of the fixture follow the regime."""
        ref = cls.env.ref
        cls.pis_tax_definition_empresa_lc.tax_id = ref("l10n_br_fiscal.tax_pis_1_65")
        cls.cofins_tax_definition_empresa_lc.tax_id = ref(
            "l10n_br_fiscal.tax_cofins_7_6"
        )

    @staticmethod
    def _access_key(number, cnpj="49190159000105"):
        """A valid 44 digits access key (check digit included) for the number,
        issued by the CNPJ (the supplier of the tests by default)."""
        base = f"352611{cnpj}55001{number.zfill(9)}1{number.zfill(8)}"
        weights = [2, 3, 4, 5, 6, 7, 8, 9]
        total = sum(
            int(digit) * weights[index % 8]
            for index, digit in enumerate(reversed(base))
        )
        check = 11 - total % 11
        return base + str(0 if check >= 10 else check)

    def _entry_document(
        self,
        document_date=datetime(2026, 7, 20, 12, 0),
        date_in_out=None,
        state_edoc="autorizada",
        operation="fo_compras",
        operation_line="fo_compras_compras_comercializacao",
        imported=True,
        partner_cfop="6102",
        line_vals=None,
        edoc_purpose=None,
        **doc_vals,
    ):
        """A supplier invoice as the import leaves it (CST of the issuer).

        ``operation="fo_venda"`` with ``imported=False`` gives an outgoing one.
        """
        fiscal_operation = self.env.ref(f"l10n_br_fiscal.{operation}")
        operation_type = fiscal_operation.fiscal_operation_type
        type(self)._doc_number += 1
        number = str(self._doc_number)
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "fiscal_operation_id": fiscal_operation.id,
                "fiscal_operation_type": operation_type,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_number": number,
                "document_serie": "1",
                "document_key": self._access_key(number),
                "issuer": "partner" if operation_type == "in" else "company",
                "partner_id": self.partner_a.id,
                "document_date": document_date,
                "date_in_out": date_in_out or document_date,
                "state_edoc": state_edoc,
                "imported_document": imported,
                **doc_vals,
            }
        )
        if edoc_purpose:
            # computed from the operation: only a write sticks
            document.edoc_purpose = edoc_purpose
        vals = {
            "document_id": document.id,
            "name": "Entry test",
            "product_id": self.product_a.id,
            "fiscal_operation_id": document.fiscal_operation_id.id,
            "fiscal_operation_line_id": self.env.ref(
                f"l10n_br_fiscal.{operation_line}"
            ).id,
            "fiscal_operation_type": operation_type,
            "quantity": 10,
            "price_unit": 100.0,
        }
        if imported:
            ref = self.env.ref
            vals.update(
                {
                    "partner_cfop_id": ref(f"l10n_br_fiscal.cfop_{partner_cfop}").id,
                    "icms_origin": "0",
                    "icms_tax_id": ref("l10n_br_fiscal.tax_icms_12").id,
                    "icms_cst_id": ref("l10n_br_fiscal.cst_icms_00").id,
                    "icms_base": 1000.0,
                    "icms_percent": 12.0,
                    "icms_value": 120.0,
                    "pis_tax_id": ref("l10n_br_fiscal.tax_pis_1_65").id,
                    "pis_cst_id": ref("l10n_br_fiscal.cst_pis_01").id,
                    "pis_base": 1000.0,
                    "pis_percent": 1.65,
                    "pis_value": 16.5,
                    "cofins_tax_id": ref("l10n_br_fiscal.tax_cofins_7_6").id,
                    "cofins_cst_id": ref("l10n_br_fiscal.cst_cofins_01").id,
                    "cofins_base": 1000.0,
                    "cofins_percent": 7.6,
                    "cofins_value": 76.0,
                }
            )
        vals.update(line_vals or {})
        line = self.env["l10n_br_fiscal.document.line"].create(vals)
        return document, line

    def _declaration(self, kind, dt_ini, dt_fin):
        """A declaration of the given kind, pulled from Odoo."""
        self.env["l10n_br_sped.mixin"]._flush_registers(kind)
        declaration = self.env[f"l10n_br_sped.{kind}.0000"].create(
            {
                "company_id": self.company.id,
                "DT_INI": dt_ini,
                "DT_FIN": dt_fin,
            }
        )
        declaration.button_populate_sped_from_odoo()
        return declaration

    def _sped_records(self, declaration, register):
        """The registers of one kind in the generated file, as a list of
        {field name: text}, named by the order of the layout of the register."""
        kind = declaration._get_kind()
        pattern = re.compile(rf"^l10n_br_sped\.{kind}\.\d+\.{register.lower()}$")
        spec = next(name for name in self.env.registry if pattern.match(name))
        names = [
            name for name, _field in self.env[spec]._ordered_fields() if name.isupper()
        ]
        text = declaration._generate_sped_text()
        lines = [line for line in text.splitlines() if line.startswith(f"|{register}|")]
        _logger.info("EVIDENCE %s: %s", register, lines)
        return [dict(zip(names, line.split("|")[2:-1], strict=False)) for line in lines]

    def _purchase_move(
        self, operation_line, number, payment_term=None, invoice_date=None
    ):
        """A posted supplier bill with its fiscal document authorized (the
        document of an invoice, as the user launches it)."""
        ref = self.env.ref
        bill = self.init_invoice(
            "in_invoice",
            partner=self.partner_a,
            invoice_date=invoice_date or date(2026, 7, 10),
            products=[self.product_a],
            document_type=ref("l10n_br_fiscal.document_55"),
            fiscal_operation=ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[ref(f"l10n_br_fiscal.{operation_line}")],
            document_serie="1",
            document_number=number,
        )
        if payment_term:
            with Form(bill) as bill_form:
                bill_form.invoice_payment_term_id = ref(f"account.{payment_term}")
        bill.action_post()
        bill.fiscal_document_id.write(
            {"state_edoc": "autorizada", "document_key": self._access_key(number)}
        )
        return bill
