# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command
from odoo.tests import TransactionCase, tagged

DEPENDENCIES = [
    "account_reconcile_oca",
    "web_responsive",
    "account_usability",
    "base_technical_features",
]


@tagged("post_install", "-at_install")
class TestSetup(TransactionCase):
    """The setup applies its configuration by installing the usability modules."""

    def test_usability_modules_are_installed(self):
        modules = self.env["ir.module.module"].search([("name", "in", DEPENDENCIES)])
        self.assertEqual(
            sorted(modules.mapped("name")),
            sorted(DEPENDENCIES),
            "A usability module is missing from the database",
        )
        self.assertEqual(
            set(modules.mapped("state")),
            {"installed"},
            "Every usability module must be installed with the setup",
        )

    def test_technical_menu_without_debug_mode(self):
        """Technical Features shows the menus restricted to debug mode.

        The setup pulls base_technical_features so that the technical menus are
        reachable without the debug mode; this checks the effect on a menu that
        only the technical group can see.
        """
        action = self.env["ir.actions.act_window"].create(
            {"name": "Technical action (test)", "res_model": "res.partner"}
        )
        menu = self.env["ir.ui.menu"].create(
            {
                "name": "Technical menu (test)",
                "action": f"{action._name},{action.id}",
                "group_ids": [Command.set(self.env.ref("base.group_no_one").ids)],
            }
        )
        menus = self.env["ir.ui.menu"]
        self.assertNotIn(menu.id, menus._visible_menu_ids())
        self.env.user.technical_features = True
        self.assertIn(menu.id, menus._visible_menu_ids())

    def test_account_tags_menu_is_available(self):
        """account_usability exposes the account tags, used by the BR charts."""
        action = self.env.ref("account_usability.account_account_tag_action")
        self.assertEqual(action.res_model, "account.account.tag")
