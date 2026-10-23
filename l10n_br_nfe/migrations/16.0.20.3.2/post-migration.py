# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Mark the anonymous consumer partner as such.

    The record l10n_br_fiscal.res_partner_anonimo is noupdate, so the
    databases that already have it do not receive the new data.
    """
    partner = env.ref("l10n_br_fiscal.res_partner_anonimo", raise_if_not_found=False)
    if partner:
        partner.write({"is_anonymous_consumer": True})
