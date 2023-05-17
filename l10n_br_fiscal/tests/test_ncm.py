# @ 2023 Engenere - https://engenere.one/ -
#   Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestNcm(TransactionCase):
    def setUp(self):
        super(TestNcm, self).setUp()

        # Create a test user with manager rights
        self.test_user_manager = self.env["res.users"].create(
            {
                "name": "Test User Manager",
                "login": "test_user_manager",
                "groups_id": [
                    (6, 0, [self.env.ref("l10n_br_fiscal.group_manager").id])
                ],
            }
        )

        # Create a test user without manager rights
        self.test_user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
            }
        )

        # Fetch an existing record
        self.test_record = self.env.ref("l10n_br_fiscal.ncm_00000000")

    def test_action_archive_manager(self):
        self.test_record.with_user(self.test_user_manager).action_archive()
        self.assertFalse(self.test_record.active, "Record should be archived")

    def test_action_unarchive_manager(self):
        self.test_record.with_user(self.test_user_manager).action_unarchive()
        self.assertTrue(self.test_record.active, "Record should be unarchived")

    def test_action_archive_no_rights(self):
        with self.assertRaises(AccessError):
            self.test_record.with_user(self.test_user).action_archive()

    def test_action_unarchive_no_rights(self):
        with self.assertRaises(AccessError):
            self.test_record.with_user(self.test_user).action_unarchive()
