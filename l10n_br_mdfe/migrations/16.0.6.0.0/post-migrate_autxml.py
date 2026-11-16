# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Move the autXML authorizations from res_partner to their own model.

    The autXML tag used to be stacked into res.partner, which materialized
    the res_partner.mdfe30_autXML_infMDFe_id column. Being a single column, a
    partner could only ever hold one authorization, and deleting a document
    cascaded into deleting the partner.

    This runs as a post script because the l10n_br_mdfe_autxml table only
    exists after the module _auto_init.
    """
    if not openupgrade.column_exists(env.cr, "res_partner", "mdfe30_autXML_infMDFe_id"):
        return

    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO l10n_br_mdfe_autxml (
            "mdfe30_autXML_infMDFe_id", partner_id,
            create_uid, create_date, write_uid, write_date
        )
        SELECT
            partner."mdfe30_autXML_infMDFe_id", partner.id,
            partner.create_uid, partner.create_date,
            partner.write_uid, partner.write_date
        FROM res_partner partner
        JOIN l10n_br_fiscal_document document
          ON document.id = partner."mdfe30_autXML_infMDFe_id"
        """,
    )

    # The orphan column still carries an ON DELETE CASCADE towards the
    # document: leaving it behind would keep the original bug armed.
    openupgrade.drop_columns(env.cr, [("res_partner", "mdfe30_autXML_infMDFe_id")])
