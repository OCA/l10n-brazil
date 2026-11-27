## Import wizard removed

The import wizard `l10n_br_fiscal.document.import.wizard`, its grid
`l10n_br_fiscal.document.import.wizard.line` and every extension of them
(`l10n_br_nfe`, `l10n_br_cte`, `l10n_br_mdfe`, `l10n_br_account`,
`l10n_br_nfse_dfe`) are removed. Fiscal files are imported by the window of
`l10n_br_fiscal_edi` (`l10n_br_fiscal_edi.document.import.wizard`, which only
has the files), into a draft document that is reviewed line by line, and the
vendor bill is generated from the document by `l10n_br_account_edi`.

**A module that inherits the wizard does not load any more.** An `_inherit =
"l10n_br_fiscal.document.import.wizard"` (or of the line) in a customization
makes the database fail to load: remove it or adapt it to the table below
before updating. A view that inherits one of the removed views is deleted with
it by the update.

### Before and after

| Before | After |
|---|---|
| `_detect_binding`, `_extract_binding_data`, `_extract_key_information`, `_destination_partner_from_binding` | `_edi_import_read`, which returns an `EdiParsedFile` |
| `_create_edoc_from_file` | `_edi_import_create` |
| `_find_existing_document` (no company) | `_edi_import_find_existing` (key and company) |
| `_import_edoc`, `action_import_and_open_document` | `_edi_import_files` and the window `l10n_br_fiscal_edi.document.import.wizard` |
| `_parse_file_data` (base64) | the parse is done by the reader, on bytes |
| `_find_fiscal_operation(_line)`, `_counterpart_cfop_code`, `_most_common_cfop` | `l10n_br_fiscal.operation.line._find_by_issuer_cfop` and `l10n_br_fiscal.document._suggest_fiscal_operation` |
| `_match_uom_by_code` | `uom.uom._match_by_fiscal_code` |
| `_search_partner` | the partner of the binding (the reader matches by CNPJ or CPF); in the NFS-e, `_nfse_find_partner` |
| the grid `l10n_br_fiscal.document.import.wizard.line` | the review on the line of the document (`import_state`, `import_uom_id`, `import_uom_factor`, `action_resolve_line`) |
| `allow_product_creation` | does not exist: the import never creates a product |
| `date_in_out` and `fiscal_operation_id` of the wizard | fields of the document; the operation is suggested |
| `action_import_and_open_move`, `_get_importer_action`, `first_imported_move_id` | `create_document_from_attachment` and `action_generate_invoice` (`l10n_br_account_edi`) |
| `product_id` of the NFS-e wizard | `res.company.nfse_import_product_id` (`l10n_br_nfse`) |
| the CT-e wizard | the company is looked for as taker, recipient, sender |
| the MDF-e wizard | the issuing company, an own document of output |
| the inbox opening the wizard with `default_file` | the generic `import_document()` of `l10n_br_fiscal_dfe`, with `attachment.raw` |

### Removed from the database

- Models (`ir.model`): `l10n_br_fiscal.document.import.wizard` and
  `l10n_br_fiscal.document.import.wizard.line`.
- Views and actions:
  - `l10n_br_fiscal.document_import_wizard_form`;
  - `l10n_br_nfe.document_import_wizard_form`,
    `l10n_br_nfe.l10n_br_nfe_import_xml_products_tree`,
    `l10n_br_nfe.l10n_br_nfe_import_xml_action`,
    `l10n_br_nfe.nfe_import_document`, `l10n_br_nfe.imported_document_menu`,
    `l10n_br_nfe.imported_document_action` (the menus "Import fiscal document"
    and "Imported documents" of `l10n_br_fiscal_edi` replace them);
  - `l10n_br_account.document_import_wizard_form`;
  - `l10n_br_nfse_dfe.document_import_wizard_form_nfse`.
- Access rules: `l10n_br_fiscal_document_import_wizard_user` and
  `l10n_br_fiscal_document_import_wizard_line_user`.

### Documents already imported

The lines of the documents that the old wizard imported have no review state. A
post-migration marks them as resolved (the grid of the wizard was their review), so
that their invoice can be generated from the new screen.
