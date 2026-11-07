# Copyright 2026 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.tests import Form, TransactionCase, tagged


class TestFiscalDataValidity(TransactionCase):
    """Validity window (date_start/date_end) for `l10n_br_fiscal.data.abstract`
    descendants, exercised through `l10n_br_fiscal.ncm`."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Ncm = cls.env["l10n_br_fiscal.ncm"]
        cls.today = fields.Date.context_today(cls.Ncm)

    def _create_ncm(self, code, **kwargs):
        vals = {"code": code, "name": "Test NCM %s" % code}
        vals.update(kwargs)
        return self.Ncm.create(vals)

    def test_no_dates_stay_active(self):
        ncm = self._create_ncm("11111111")
        ncm._expire_invalid_records()
        self.assertTrue(ncm.active)

    def test_future_start_date_stays_active(self):
        ncm = self._create_ncm(
            "22222222", date_start=fields.Date.add(self.today, days=5)
        )
        ncm._expire_invalid_records()
        self.assertTrue(ncm.active)

    def test_past_end_date_expires(self):
        ncm = self._create_ncm(
            "33333333", date_end=fields.Date.subtract(self.today, days=1)
        )
        ncm._expire_invalid_records()
        self.assertFalse(ncm.active)

    def test_within_range_stays_active(self):
        ncm = self._create_ncm(
            "44444444",
            date_start=fields.Date.subtract(self.today, days=1),
            date_end=fields.Date.add(self.today, days=1),
        )
        ncm._expire_invalid_records()
        self.assertTrue(ncm.active)

    def test_only_start_date_in_the_past_stays_active(self):
        ncm = self._create_ncm(
            "55555555", date_start=fields.Date.subtract(self.today, days=1)
        )
        ncm._expire_invalid_records()
        self.assertTrue(ncm.active)


class TestTaxDefinitionValidity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Datetime.now()

    def _create_tax_definition(self, code, **kwargs):
        vals = {
            "tax_group_id": self.env.ref("l10n_br_fiscal.tax_group_icms").id,
            "code": code,
            "name": "Test Tax Definition %s" % code,
            "state": "approved",
        }
        vals.update(kwargs)
        return self.env["l10n_br_fiscal.tax.definition"].create(vals)

    def _create_future_tax_definition(self, code):
        return self._create_tax_definition(
            code,
            date_start=fields.Datetime.add(self.today, days=5),
            state_from_id=self.env.ref("base.state_br_sp").id,
            state_to_ids=[Command.set(self.env.ref("base.state_br_mg").ids)],
        )

    def _map(self, tax_definition, reference_date=None):
        return tax_definition.map_tax_definition(
            self.env.ref("l10n_br_base.empresa_lucro_presumido"),
            self.env.ref("l10n_br_base.res_partner_cliente9_mg"),
            self.env.ref("product.product_product_7"),
            city_taxation_code=self.env["l10n_br_fiscal.city.taxation.code"],
            national_taxation_code=self.env["l10n_br_fiscal.national.taxation.code"],
            service_type=self.env["l10n_br_fiscal.service.type"],
            reference_date=reference_date,
        )

    def test_map_tax_definition_excludes_out_of_validity_records(self):
        tax_definition = self._create_future_tax_definition("TDV003")
        self.assertNotIn(tax_definition, self._map(tax_definition))

    def test_future_rule_is_found_on_its_date(self):
        tax_definition = self._create_future_tax_definition("TDV004")
        self.assertIn(
            tax_definition,
            self._map(tax_definition, fields.Datetime.add(self.today, days=6)),
        )


@tagged("post_install", "-at_install")
class TestDocumentReferenceDate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.today = fields.Datetime.now()
        cls.tax_ipi_nt = cls.env.ref("l10n_br_fiscal.tax_ipi_nt")
        cls.env.ref("l10n_br_fiscal.fo_venda_revenda_ipi_nt").write(
            {
                "date_start": fields.Datetime.subtract(cls.today, days=90),
                "date_end": fields.Datetime.subtract(cls.today, days=30),
            }
        )

    def _new_line_taxes(self, document_date):
        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
            )
        )
        doc_form.company_id = self.company
        doc_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        doc_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        doc_form.document_date = document_date
        with doc_form.fiscal_line_ids.new() as line_form:
            line_form.product_id = self.env.ref("product.product_product_6")
            return line_form.fiscal_tax_ids

    def test_backdated_document_uses_rule_valid_on_its_date(self):
        backdated = fields.Datetime.subtract(self.today, days=60)
        self.assertIn(self.tax_ipi_nt, self._new_line_taxes(backdated))
        self.assertNotIn(self.tax_ipi_nt, self._new_line_taxes(self.today))

    def test_changing_the_document_date_maps_the_lines_again(self):
        """The line is mapped when it is added; the date typed afterwards has to
        map it again, otherwise the taxes stay on the date it had before."""
        backdated = fields.Datetime.subtract(self.today, days=60)
        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
            )
        )
        doc_form.company_id = self.company
        doc_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        doc_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        doc_form.document_date = self.today
        with doc_form.fiscal_line_ids.new() as line_form:
            line_form.product_id = self.env.ref("product.product_product_6")
            self.assertNotIn(self.tax_ipi_nt, line_form.fiscal_tax_ids)
        doc_form.document_date = backdated
        with doc_form.fiscal_line_ids.edit(0) as line_form:
            self.assertIn(self.tax_ipi_nt, line_form.fiscal_tax_ids)
        doc_form.document_date = self.today
        with doc_form.fiscal_line_ids.edit(0) as line_form:
            self.assertNotIn(self.tax_ipi_nt, line_form.fiscal_tax_ids)
