# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    """The special regime of the NFS-e was always "1" (municipal micro
    company): keep it for the companies that issued NFS-e with it."""
    cr.execute(
        """
        UPDATE res_company company
        SET nfse_taxation_special_regime = '1'
        WHERE company.nfse_taxation_special_regime IS NULL
            AND EXISTS (
                SELECT 1
                FROM l10n_br_fiscal_document document
                JOIN l10n_br_fiscal_document_type document_type
                    ON document_type.id = document.document_type_id
                WHERE document.company_id = company.id
                    AND document_type.code = 'SE'
                    AND document.taxation_special_regime = '1'
                    AND document.state_edoc IN ('autorizada', 'cancelada')
            )
        """
    )
