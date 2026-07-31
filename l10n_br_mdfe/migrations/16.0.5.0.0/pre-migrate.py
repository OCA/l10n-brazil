def migrate(cr, version):
    # Remove stale relation tables from previous field definitions
    cr.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'mdfe_m2m_nfe_rel'
        )
    """
    )
    if cr.fetchone()[0]:
        cr.execute("DROP TABLE mdfe_m2m_nfe_rel CASCADE")

    cr.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'mdfe_m2m_cte_rel'
        )
    """
    )
    if cr.fetchone()[0]:
        cr.execute("DROP TABLE mdfe_m2m_cte_rel CASCADE")

    cr.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'mdfe_m2m_mdfe_rel'
        )
    """
    )
    if cr.fetchone()[0]:
        cr.execute("DROP TABLE mdfe_m2m_mdfe_rel CASCADE")

    # Remove stale field records from ir_model_fields
    cr.execute(
        """
        DELETE FROM ir_model_fields
        WHERE name IN ('mdfe_nfe_ids', 'mdfe_cte_ids', 'mdfe_mdfe_ids', 'mdfe_ids')
        AND model = 'l10n_br_fiscal.document'
    """
    )

    # Update any view arch that still references old field names
    for old_name in ("mdfe_nfe_ids", "mdfe_cte_ids", "mdfe_mdfe_ids"):
        cr.execute(
            """
            UPDATE ir_ui_view
            SET arch_db = REPLACE(arch_db::text, %s, 'mdfe_document_ids')::jsonb
            WHERE arch_db::text LIKE %s
        """,
            [old_name, "%" + old_name + "%"],
        )
