# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.exceptions import ValidationError

from .common import (
    CNPJ_1,
    CNPJ_2,
    CPF_1,
    CPF_1_FORMATTED,
    CPF_2,
    CPF_3,
    CPF_4,
    FOREIGN_VAT,
    IE_BA,
    IE_SP,
    L10nBrBaseCase,
)


class PartnerVatTest(L10nBrBaseCase):
    def test_br_vat_stored_unformatted(self):
        partner = self._person(vat=CPF_1_FORMATTED)
        self.assertEqual(partner.vat, CPF_1)
        self.assertEqual(partner.cnpj_cpf_stripped, CPF_1)
        self.assertEqual(partner.vat_formatted_cnpj, CPF_1_FORMATTED)

    def test_foreign_vat_kept_as_typed(self):
        partner = self._company(country_id=self.us.id, vat=FOREIGN_VAT)
        self.assertEqual(partner.vat, FOREIGN_VAT)
        self.assertFalse(partner.vat_formatted_cnpj)

    def test_write_vat_on_br_partner_unformatted(self):
        partner = self._person()
        partner.vat = CPF_1_FORMATTED
        self.assertEqual(partner.vat, CPF_1)

    def test_write_vat_with_country_in_same_write(self):
        partner = self.partner_model.create(
            {"name": "Moving to Brazil", "country_id": self.us.id}
        )
        partner.write({"country_id": self.br.id, "vat": CPF_1_FORMATTED})
        self.assertEqual(partner.vat, CPF_1)

    def test_onchange_vat_unformats(self):
        partner = self.partner_model.new(
            {"name": "Draft", "country_id": self.br.id, "vat": CPF_1_FORMATTED}
        )
        partner._onchange_vat()
        self.assertEqual(partner.vat, CPF_1)

    def test_invalid_cpf_rejected(self):
        with self.assertRaises(ValidationError):
            self._person(vat="063.109.997-20")

    def test_repeated_digits_cpf_rejected(self):
        with self.assertRaises(ValidationError):
            self._person(vat="222.222.222-22")

    def test_invalid_size_rejected(self):
        with self.assertRaises(ValidationError):
            self._person(vat="12345")

    def test_cpf_validation_disabled_by_setting(self):
        self.config.set_param("l10n_br_base.disable_cpf_cnpj_validation", True)
        partner = self._person(vat="22222222222")
        self.assertEqual(partner.vat, "22222222222")

    def test_cpf_validation_disabled_by_context(self):
        partner = self.partner_model.with_context(
            disable_cpf_cnpj_validation=True
        ).create({"name": "No check", "country_id": self.br.id, "vat": "22222222222"})
        self.assertEqual(partner.vat, "22222222222")

    def test_foreign_vat_not_validated_as_cpf(self):
        partner = self._company(country_id=self.us.id, vat="123")
        self.assertEqual(partner.vat, "123")

    def test_duplicate_cpf_rejected(self):
        self._person(vat=CPF_1)
        with self.assertRaises(ValidationError):
            self._person(name="Another Person", vat=CPF_1)

    def test_contact_may_share_company_cnpj(self):
        company = self._company(vat=CNPJ_1)
        contact = self.partner_model.create(
            {"name": "Contact", "parent_id": company.id, "vat": CNPJ_1}
        )
        self.assertEqual(contact.vat, CNPJ_1)

    def test_is_br_partner(self):
        self.assertTrue(self._person().is_br_partner)
        without_country = self.partner_model.create(
            {"name": "No Country", "country_id": False, "vat": CPF_2}
        )
        self.assertTrue(without_country.is_br_partner)
        foreign = self._company(country_id=self.us.id, vat=FOREIGN_VAT)
        self.assertFalse(foreign.is_br_partner)

    def test_show_l10n_br_follows_partner_country(self):
        self.assertTrue(self._person().show_l10n_br)
        self.assertFalse(self._person(country_id=self.us.id).show_l10n_br)

    def test_show_br_vat_format_follows_current_company(self):
        partner = self._person()
        us_company = self.env["res.company"].create(
            {"name": "US Company", "country_id": self.us.id}
        )
        self.assertTrue(partner.show_br_vat_format)
        self.assertFalse(partner.with_company(us_company).show_br_vat_format)

    def test_default_country_from_current_company(self):
        partner = self.partner_model.create({"name": "Default Country"})
        self.assertEqual(partner.country_id, self.br)
        us_company = self.env["res.company"].create(
            {"name": "US Company", "country_id": self.us.id}
        )
        partner_us = self.partner_model.with_company(us_company).create(
            {"name": "No Default Country"}
        )
        self.assertFalse(partner_us.country_id)


class PartnerSearchTest(L10nBrBaseCase):
    def _found(self, text):
        return [res[0] for res in self.partner_model.name_search(text)]

    def test_name_search_by_legal_name(self):
        partner = self._company(
            name="Trade Name", legal_name="Razao Social Exclusiva de Teste Ltda"
        )
        self.assertIn(partner.id, self._found("Exclusiva de Teste"))

    def test_name_search_by_unmasked_cnpj(self):
        partner = self._company(name="Searchable", vat=CNPJ_1)
        self.assertIn(partner.id, self._found(CNPJ_1))

    def test_name_search_by_state_tax_number(self):
        partner = self._company(
            name="With IE", state_id=self.state_sp.id, l10n_br_ie_code=IE_SP
        )
        self.assertIn(partner.id, self._found(IE_SP))


class PartnerAddressTest(L10nBrBaseCase):
    def test_br_street_uses_comma(self):
        partner = self._person(
            street_name="Rua Acre", street_number="47", street_number2="Sala 1310"
        )
        self.assertEqual(partner.street, "Rua Acre, 47 - Sala 1310")

    def test_foreign_street_uses_core_format(self):
        partner = self._person(
            country_id=self.us.id,
            street_name="Main Street",
            street_number="10",
            street_number2="Apt 2",
        )
        self.assertEqual(partner.street, "Main Street 10 - Apt 2")

    def test_district_synced_to_contact(self):
        company = self._company(
            district="Centro", state_id=self.state_sp.id, city_id=self.city_sp.id
        )
        contact = self.partner_model.create(
            {"name": "Contact", "parent_id": company.id, "type": "contact"}
        )
        self.assertEqual(contact.district, "Centro")
        company.district = "Bela Vista"
        self.assertEqual(contact.district, "Bela Vista")

    def test_onchange_city_sets_city_name(self):
        partner = self.partner_model.new(
            {
                "country_id": self.br.id,
                "state_id": self.state_sp.id,
                "city_id": self.city_sp.id,
            }
        )
        partner._onchange_city_id()
        self.assertEqual(partner.city, "São Paulo")

    def test_onchange_state_clears_city(self):
        partner = self.partner_model.new(
            {
                "country_id": self.br.id,
                "state_id": self.state_rj.id,
                "city_id": self.city_sp.id,
            }
        )
        partner._onchange_state_id()
        self.assertFalse(partner.city_id)

    def test_onchange_zip_formats_br_zip(self):
        partner = self.partner_model.new({"country_id": self.br.id, "zip": "01311915"})
        partner._onchange_zip()
        self.assertEqual(partner.zip, "01311-915")


class PartnerCommercialSyncTest(L10nBrBaseCase):
    def test_br_company_cnpj_not_synced_to_contact(self):
        company = self._company(vat=CNPJ_1)
        contact = self.partner_model.create(
            {"name": "Contact", "parent_id": company.id}
        )
        self.assertFalse(contact.vat)
        company.vat = CNPJ_2
        self.assertFalse(contact.vat)

    def test_foreign_company_vat_synced_to_contact(self):
        company = self._company(country_id=self.us.id, vat=FOREIGN_VAT)
        contact = self.partner_model.create(
            {"name": "Contact", "parent_id": company.id, "country_id": self.us.id}
        )
        self.assertEqual(contact.vat, FOREIGN_VAT)
        company.vat = "98-7654321"
        self.assertEqual(contact.vat, "98-7654321")

    def test_br_contact_does_not_get_foreign_company_vat(self):
        company = self._company(country_id=self.us.id, vat=FOREIGN_VAT)
        contact = self.partner_model.create(
            {"name": "Contact", "parent_id": company.id, "type": "other"}
        )
        self.assertEqual(contact.country_id, self.br)
        self.assertFalse(contact.vat)

    def test_br_company_commercial_fields_synced_to_contact(self):
        industry_1, industry_2 = self.env["res.partner.industry"].create(
            [{"name": "Industry 1"}, {"name": "Industry 2"}]
        )
        company = self._company(vat=CNPJ_1, industry_id=industry_1.id)
        contact = self.partner_model.create(
            {"name": "Contact", "parent_id": company.id}
        )
        self.assertEqual(contact.industry_id, industry_1)
        company.industry_id = industry_2
        self.assertEqual(contact.industry_id, industry_2)


class PartnerCopyTest(L10nBrBaseCase):
    def test_copy_br_person_clears_vat(self):
        copied = self._person(vat=CPF_1).copy()
        self.assertFalse(copied.vat)

    def test_copy_foreign_company_keeps_vat(self):
        copied = self._company(country_id=self.us.id, vat=FOREIGN_VAT).copy()
        self.assertEqual(copied.vat, FOREIGN_VAT)

    def test_copy_with_explicit_vat(self):
        copied = self._person(vat=CPF_1).copy({"vat": CPF_2})
        self.assertEqual(copied.vat, CPF_2)

    def test_copy_multi_br_partners(self):
        """Copying several Brazilian partners at once (Duplicate action of the
        list) works and does not duplicate the CPF/CNPJ."""
        partners = self._person(name="Person 1", vat=CPF_3) | self._person(
            name="Person 2", vat=CPF_4
        )
        copies = partners.copy()
        self.assertEqual(len(copies), 2)
        self.assertFalse(any(copies.mapped("vat")))


class StateTaxNumberTest(L10nBrBaseCase):
    def test_invalid_company_ie_rejected(self):
        with self.assertRaises(ValidationError):
            self._company(state_id=self.state_sp.id, l10n_br_ie_code="123456")

    def test_valid_company_ie_accepted(self):
        partner = self._company(state_id=self.state_sp.id, l10n_br_ie_code=IE_SP)
        self.assertEqual(partner.l10n_br_ie_code, IE_SP)

    def test_exempt_ie_accepted(self):
        for value in ("ISENTO", "isento", "ISENTA", "isenta"):
            with self.subTest(value=value):
                partner = self._company(
                    state_id=self.state_sp.id, l10n_br_ie_code=value
                )
                self.assertEqual(partner.l10n_br_ie_code, value)

    def test_ie_validation_disabled_by_setting(self):
        self.config.set_param("l10n_br_base.disable_ie_validation", True)
        partner = self._company(state_id=self.state_sp.id, l10n_br_ie_code="123456")
        self.assertEqual(partner.l10n_br_ie_code, "123456")

    def test_person_ie_not_validated(self):
        partner = self._person(state_id=self.state_sp.id, l10n_br_ie_code="123456")
        self.assertEqual(partner.l10n_br_ie_code, "123456")

    def test_other_ie_used_as_main_ie_elsewhere_rejected(self):
        self._company(
            name="Company BA", state_id=self.state_ba.id, l10n_br_ie_code=IE_BA
        )
        other = self._company(name="Company SP", state_id=self.state_sp.id)
        with self.assertRaises(ValidationError):
            other.write(
                {
                    "state_tax_number_ids": [
                        (0, 0, {"state_id": self.state_ba.id, "l10n_br_ie_code": IE_BA})
                    ]
                }
            )

    def test_partner_adds_second_other_ie(self):
        """Revalidating the partner's existing lines must not match the
        partner itself."""
        partner = self._company(
            state_id=self.state_sp.id,
            state_tax_number_ids=[
                (0, 0, {"state_id": self.state_ba.id, "l10n_br_ie_code": IE_BA})
            ],
        )
        partner.with_context(disable_ie_validation=True).write(
            {
                "state_tax_number_ids": [
                    (0, 0, {"state_id": self.state_rj.id, "l10n_br_ie_code": "12345"})
                ]
            }
        )
        self.assertEqual(len(partner.state_tax_number_ids), 2)
