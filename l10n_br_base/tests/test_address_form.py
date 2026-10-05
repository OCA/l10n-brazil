# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree

from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAddressForm(TransactionCase):
    """The address form has to follow two countries at the same time: the
    core swaps in the address view of the country of the CURRENT COMPANY
    (_view_get_address: "consider the country of the user, not the country of
    the partner"), and the fields of that view have to follow the country of
    the ADDRESS being typed. So the Brazilian fields must be editable with a
    foreign current company, and a foreign address must stay editable with a
    Brazilian current company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.br = cls.env.ref("base.br")
        cls.us = cls.env.ref("base.us")
        cls.fr = cls.env.ref("base.fr")
        cls.foreign_company = cls.env["res.company"].create(
            {"name": "Foreign Company", "country_id": cls.us.id}
        )
        cls.br_company = cls.env["res.company"].create(
            {"name": "Brazilian Company", "country_id": cls.br.id}
        )
        # with account installed the partner form requires the receivable and
        # payable accounts of the company
        if "account.chart.template" in cls.env:
            for company in (cls.foreign_company, cls.br_company):
                cls.env["account.chart.template"].try_loading(
                    "generic_coa", company, install_demo=False
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

    def test_company_form_foreign_city(self):
        """res.city only holds Brazilian cities, so the free text city of the
        core is the only one a foreign company can fill."""
        company_form = Form(self.foreign_company.with_company(self.foreign_company))
        company_form.city = "Chicago"
        company = company_form.save()
        self.assertEqual(company.city, "Chicago")

    def test_foreign_partner_keeps_street_brazilian_company(self):
        """With a Brazilian current company the core swaps in the Brazilian
        address view for every record, whatever its country: a foreign address
        is still a single street line."""
        partner_form = Form(self.env["res.partner"].with_company(self.br_company))
        partner_form.name = "Foreign Customer"
        partner_form.country_id = self.us
        partner_form.street = "1600 Amphitheatre Parkway"
        partner = partner_form.save()
        self.assertEqual(partner.street, "1600 Amphitheatre Parkway")

    def test_foreign_company_keeps_street_brazilian_company(self):
        company_form = Form(self.foreign_company.with_company(self.br_company))
        company_form.street = "1600 Amphitheatre Parkway"
        company = company_form.save()
        self.assertEqual(company.street, "1600 Amphitheatre Parkway")
        self.assertEqual(company.partner_id.street, "1600 Amphitheatre Parkway")

    def test_partner_form_brazilian_company(self):
        """The Brazilian address itself keeps being typed in street name,
        number and district."""
        partner_form = Form(self.env["res.partner"].with_company(self.br_company))
        partner_form.name = "Cliente BR"
        partner_form.country_id = self.br
        partner_form.street_name = "Rua Samuel Morse"
        partner_form.street_number = "134"
        partner_form.district = "Brooklin"
        partner = partner_form.save()
        self.assertEqual(partner.street, "Rua Samuel Morse, 134")
        self.assertEqual(partner.district, "Brooklin")

    def test_company_country_change_drops_foreign_state(self):
        """A country with no federal states, such as France, must not keep the
        state of the previous country: the core does it on res.partner, not on
        res.company."""
        illinois = self.env["res.country.state"].search(
            [("country_id", "=", self.us.id), ("code", "=", "IL")], limit=1
        )
        company = self.env["res.company"].create(
            {"name": "Chicago Branch", "country_id": self.us.id}
        )
        company.state_id = illinois
        company_form = Form(company.with_company(self.br_company))
        company_form.country_id = self.fr
        self.assertFalse(company_form.state_id)
