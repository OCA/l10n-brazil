# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree

from odoo.tests import Form, TransactionCase


class TestAddressForm(TransactionCase):
    """The Brazilian address fields must be editable on the forms whatever
    the country of the current company: the core only swaps in the address
    view of the country (address_view_id) when the current company is from
    that country."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.br = cls.env.ref("base.br")
        cls.us = cls.env.ref("base.us")
        cls.foreign_company = cls.env["res.company"].create(
            {"name": "Foreign Company", "country_id": cls.us.id}
        )
        cls.br_company = cls.env["res.company"].create(
            {"name": "Brazilian Company", "country_id": cls.br.id}
        )

    def _form_arch(self, model, company):
        views = self.env[model].with_company(company).get_views([(False, "form")])
        return etree.fromstring(views["views"]["form"]["arch"])

    def test_street_number_in_partner_and_company_forms(self):
        for company in (self.foreign_company, self.br_company):
            for model in ("res.partner", "res.company"):
                with self.subTest(company=company.name, model=model):
                    arch = self._form_arch(model, company)
                    self.assertTrue(arch.xpath("//field[@name='street_number']"))

    def test_partner_form_foreign_company(self):
        partner_form = Form(self.env["res.partner"].with_company(self.foreign_company))
        partner_form.name = "Cliente BR"
        partner_form.country_id = self.br
        partner_form.street_name = "Rua Samuel Morse"
        partner_form.street_number = "134"
        partner_form.district = "Brooklin"
        with partner_form.child_ids.new() as child:
            child.type = "delivery"
            child.name = "Entrega"
            child.country_id = self.br
            child.street_name = "Avenida Paulista"
            child.street_number = "807"
        partner = partner_form.save()
        self.assertEqual(partner.street, "Rua Samuel Morse, 134")
        self.assertEqual(partner.district, "Brooklin")
        self.assertEqual(partner.child_ids.street, "Avenida Paulista, 807")

    def test_foreign_partner_keeps_street(self):
        partner_form = Form(self.env["res.partner"].with_company(self.foreign_company))
        partner_form.name = "Foreign Customer"
        partner_form.country_id = self.us
        partner_form.street = "1600 Amphitheatre Parkway"
        partner = partner_form.save()
        self.assertEqual(partner.street, "1600 Amphitheatre Parkway")

    def test_company_form_foreign_company(self):
        company_form = Form(self.br_company.with_company(self.foreign_company))
        company_form.street_name = "Rua Paulo Dias"
        company_form.street_number = "586"
        company = company_form.save()
        self.assertEqual(company.street_number, "586")
        self.assertEqual(company.partner_id.street_number, "586")
        self.assertEqual(company.partner_id.street, "Rua Paulo Dias, 586")

    def test_company_created_from_partner(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Empresa Teste Ltda",
                "is_company": True,
                "country_id": self.br.id,
                "street_name": "Rua Paulo Dias",
                "street_number": "586",
                "district": "Vila Santa Luzia",
                "zip": "18125-000",
            }
        )
        company = self.env["res.company"].create(
            {"name": "Empresa Teste", "partner_id": partner.id}
        )
        self.env.flush_all()
        company.invalidate_recordset()
        self.assertEqual(company.street, "Rua Paulo Dias, 586")
        self.assertEqual(company.street_number, "586")
        self.assertEqual(company.district, "Vila Santa Luzia")
        self.assertEqual(company.zip, "18125-000")
