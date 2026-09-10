# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestNfseOptionalGroups(TransactionCase):
    """What the DPS may not carry: a masked NBS code and an empty group.

    Both were found comparing a real NFS-e issued through the national web
    emitter against the one this module builds for the same taker and the same
    amount.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.line = cls.env.ref("l10n_br_nfse_nacional.demo_nfse_lc").fiscal_line_ids[0]

    def test_the_nbs_code_goes_out_without_its_mask(self):
        """The catalog stores "1.2001.50.00" for display; cNBS wants 9 digits."""
        nbs = self.env["l10n_br_fiscal.nbs"].create(
            {"name": "Industrial machinery maintenance", "code": "1.2001.50.00"}
        )
        self.line.nbs_id = nbs
        self.assertEqual(self.line.nfse10_cNBS, "120015000")

    def test_an_unmasked_nbs_code_is_sent_as_it_is(self):
        nbs = self.env["l10n_br_fiscal.nbs"].create(
            {"name": "Service with no mask", "code": "222222222"}
        )
        self.line.nbs_id = nbs
        self.assertEqual(self.line.nfse10_cNBS, "222222222")

    def test_without_an_nbs_the_tag_is_left_out(self):
        self.line.nbs_id = False
        self.assertFalse(self.line.nfse10_cNBS)

    def test_the_discount_group_is_absent_when_there_is_no_discount(self):
        """Pointing the group at the line always serializes an empty tag."""
        self.line.write({"discount_value": 0.0, "issqn_desc_cond_amount": 0.0})
        self.assertFalse(self.line.nfse10_vDescCondIncond)

    def test_an_unconditional_discount_brings_the_group_back(self):
        self.line.discount_value = 10.0
        self.assertEqual(self.line.nfse10_vDescCondIncond, self.line)
        self.assertEqual(self.line.nfse10_vDescIncond, "10.00")

    def test_a_conditional_discount_brings_the_group_back(self):
        self.line.write({"discount_value": 0.0, "issqn_desc_cond_amount": 7.5})
        self.assertEqual(self.line.nfse10_vDescCondIncond, self.line)
        self.assertEqual(self.line.nfse10_vDescCond, "7.50")


class TestNfseServiceDescription(TransactionCase):
    """What the client requires inside xDescServ, since the NFS-e has no infAdProd.

    A real note issued outside Odoo carried the measurement bulletin, the contract,
    the order, the period, the cost centre, the due date and the bank details, all in
    the service description. Line level fiscal comments already render that text into
    additional_data; this is the wire from there to the tag.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.line = cls.env.ref("l10n_br_nfse_nacional.demo_nfse_lc").fiscal_line_ids[0]

    def test_without_a_composed_text_the_line_name_is_used(self):
        self.line.write({"name": "SERVICO DE MANUTENCAO", "additional_data": False})
        self.assertEqual(self.line.nfse10_xDescServ, "SERVICO DE MANUTENCAO")

    def test_a_composed_text_replaces_the_line_name(self):
        """The real note does not prefix a product name; a template asks for it."""
        self.line.write(
            {
                "name": "SERVICO DE MANUTENCAO",
                "additional_data": "CONFORME BOLETIM 057771 - CONTRATO 021925",
            }
        )
        self.assertEqual(
            self.line.nfse10_xDescServ, "CONFORME BOLETIM 057771 - CONTRATO 021925"
        )

    def test_a_text_longer_than_the_schema_allows_is_cut(self):
        self.line.write({"additional_data": "x" * 2500})
        self.assertEqual(len(self.line.nfse10_xDescServ), 2000)

    def test_a_blank_text_falls_back_instead_of_going_out_empty(self):
        self.line.write({"name": "SERVICO", "additional_data": "   "})
        self.assertEqual(self.line.nfse10_xDescServ, "SERVICO")


class TestNfseServiceCity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.line = cls.env.ref("l10n_br_nfse_nacional.demo_nfse_lc").fiscal_line_ids[0]
        cls.elsewhere = cls.env["res.city"].search(
            [("id", "!=", cls.line.company_id.city_id.id)], limit=1
        )

    def test_a_service_is_performed_where_the_taker_is(self):
        self.line.partner_id.city_id = self.elsewhere
        self.line.invalidate_recordset(["issqn_service_city_id"])
        self.assertEqual(self.line.issqn_service_city_id, self.elsewhere)
        self.assertEqual(self.line.nfse10_cLocPrestacao, self.elsewhere.ibge_code)

    def test_without_a_city_on_the_taker_it_falls_back(self):
        self.line.partner_id.city_id = False
        self.line.invalidate_recordset(["issqn_service_city_id"])
        self.assertEqual(self.line.issqn_service_city_id, self.line.issqn_fg_city_id)

    def test_the_place_of_performance_does_not_move_the_issqn(self):
        """Setting one must not drag the other: they feed different tags."""
        antes = self.line.issqn_fg_city_id
        self.line.issqn_service_city_id = self.elsewhere
        self.assertEqual(self.line.issqn_fg_city_id, antes)

    def test_whoever_did_the_job_can_correct_the_city(self):
        self.line.issqn_service_city_id = self.elsewhere
        self.assertEqual(self.line.nfse10_cLocPrestacao, self.elsewhere.ibge_code)
