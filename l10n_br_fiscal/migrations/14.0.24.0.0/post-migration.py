from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.delete_records_safely_by_xml_id(
        env, ["l10n_br_fiscal.l10n_br_fiscal_tax_estimate_rule"]
    )
