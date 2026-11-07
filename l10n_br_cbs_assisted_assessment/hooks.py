# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Issue the webhook token of companies created before this module."""
    env["res.company"].with_context(active_test=False).search(
        [("cbs_assessment_webhook_token", "=", False)]
    )._ensure_cbs_assessment_webhook_token()
