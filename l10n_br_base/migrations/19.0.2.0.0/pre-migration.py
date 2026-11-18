# Copyright 2026 - TODAY Akretion (<https://akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def _strip_vat_punctuation(cr, country_id):
    """Remove CNPJ/CPF mask characters from Brazilian partner vat values.

    The l10n_br_base refactor stores ``res.partner.vat`` unformatted (without
    ``.``, ``/`` or ``-``). Existing records created before this change may
    still hold formatted values, so strip the punctuation before the ORM
    loads the new computed fields that depend on the unformatted value.
    """
    openupgrade.logged_query(
        cr,
        """
        UPDATE res_partner
        SET vat = regexp_replace(vat, '[./-]', '', 'g')
        WHERE country_id = %s
          AND vat IS NOT NULL
          AND vat ~ '[./-]'
        """,
        (country_id,),
    )


@openupgrade.migrate()
def migrate(env, version):
    country_br = env.ref("base.br", raise_if_not_found=False)
    if not country_br:
        return
    _strip_vat_punctuation(env.cr, country_br.id)
