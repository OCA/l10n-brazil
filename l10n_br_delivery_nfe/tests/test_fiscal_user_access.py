# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0.html).

from odoo.exceptions import AccessError
from odoo.tests import Form, TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestFiscalUserAccess(TransactionCase):
    """A NF-e user without stock rights can open the fiscal document."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document = cls.env.ref("l10n_br_nfe.demo_nfe_natural_icms_7_resale")
        if cls.document.state_edoc != "em_digitacao":
            cls.document.action_document_back2draft()
        # Same NF-e schema hook used by the other tests of this module: it
        # creates the access rules of the generated NF-e spec models.
        cls.env["spec.mixin.nfe"].with_context(
            spec_schema="nfe", spec_version="40"
        )._register_hook()
        cls.fiscal_user = new_test_user(
            cls.env,
            login="l10n_br_delivery_nfe_fiscal_user",
            groups=(
                "l10n_br_fiscal.group_user,l10n_br_nfe.group_user,"
                "account.group_account_invoice"
            ),
            company_id=cls.document.company_id.id,
        )
        cls.fiscal_user.company_ids += cls.document.company_id

    def test_fiscal_user_opens_document_form(self):
        """The fiscal user opens and saves the document form with volumes."""
        self.assertFalse(self.fiscal_user.has_group("stock.group_stock_user"))
        document = self.document.with_user(self.fiscal_user)
        with Form(document) as form:
            self.assertTrue(form.document_type_id)
            form.manual_fiscal_additional_data = "Fiscal user note"
        self.assertEqual(document.manual_fiscal_additional_data, "Fiscal user note")
        # Reading the volumes is allowed, writing them stays with stock users.
        document.nfe40_vol.read(["nfe40_qVol"])
        with self.assertRaises(AccessError):
            self.env["stock.picking.vol"].with_user(self.fiscal_user).create(
                {"nfe40_qVol": "1"}
            )
