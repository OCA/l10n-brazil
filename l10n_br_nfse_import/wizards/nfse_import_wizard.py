# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class NfseImportWizard(models.TransientModel):
    """Review wizard for importing a received NFS-e as a vendor bill.

    Opened from l10n_br_nfse.received. Fields are pre-filled from the received
    record; the user adjusts partner, product and fiscal operation before
    confirming. Confirmation creates an account.move (vendor bill).
    """

    _name = "l10n_br_nfse.import.wizard"
    _description = "NFS-e Import Review Wizard"

    received_id = fields.Many2one(
        comodel_name="l10n_br_nfse.received",
        string="Received NFS-e",
        readonly=True,
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    nfse_number = fields.Char(string="NFS-e Number", readonly=True)
    verify_code = fields.Char(string="Verification Code", readonly=True)
    emission_date = fields.Datetime(string="Emission Date", readonly=True)
    document_serie = fields.Char(string="Document Serie", readonly=True)
    rps_number = fields.Char(string="RPS / DPS Number", readonly=True)

    provider_cnpj = fields.Char(string="Provider CNPJ", readonly=True)
    provider_name = fields.Char(string="Provider Name", readonly=True)
    service_value = fields.Float(string="Service Value", readonly=True, digits=(18, 2))
    service_description = fields.Text(string="Service Description", readonly=True)
    fiscal_additional_data = fields.Text(string="Additional Info", readonly=True)

    issqn_base = fields.Float(string="ISSQN Base", readonly=True, digits=(18, 2))
    issqn_percent = fields.Float(string="ISSQN %", readonly=True)
    issqn_value = fields.Float(string="ISSQN Value", readonly=True, digits=(18, 2))
    issqn_wh_percent = fields.Float(string="ISSQN Ret. %", readonly=True)
    issqn_wh_value = fields.Float(
        string="ISSQN Ret. Value", readonly=True, digits=(18, 2)
    )

    service_lc116_code = fields.Char(string="LC116 Code", readonly=True)
    service_nbs_code = fields.Char(string="NBS Code", readonly=True)
    issqn_city_ibge = fields.Char(string="Service City IBGE", readonly=True)
    civil_construction_code = fields.Char(
        string="Civil Construction Code", readonly=True
    )
    civil_construction_art = fields.Char(string="Civil Construction ART", readonly=True)

    service_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.service.type",
        string="Service Type",
        readonly=True,
        help="Resolved from the LC116 code. "
        "Used to pre-filter the product selection.",
    )
    nbs_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.nbs",
        string="NBS",
        readonly=True,
        help="Resolved from the NBS code. " "Used to pre-filter the product selection.",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        help="Service product to link to the vendor bill line. "
        "Pre-filled from the service type or NBS; adjust if needed.",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        help="Service provider. Pre-filled from the CNPJ; adjust if needed.",
    )
    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
        domain=[
            ("fiscal_operation_type", "=", "in"),
            ("state", "=", "approved"),
        ],
    )

    account_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Existing Vendor Bill",
        readonly=True,
        help="Set when a matching vendor bill already exists for this NFS-e.",
    )

    @api.model
    def default_get(self, fields_list):
        """Pre-fill all fields from the received NFS-e record."""
        vals = super().default_get(fields_list)
        received_id = self.env.context.get("default_received_id")
        if not received_id:
            return vals
        received = self.env["l10n_br_nfse.received"].browse(received_id)
        if not received.exists():
            return vals

        default_op = self._default_fiscal_operation()
        vals.update(
            {
                "received_id": received.id,
                "company_id": received.company_id.id,
                "nfse_number": received.nfse_number,
                "verify_code": received.verify_code,
                "emission_date": received.emission_date,
                "document_serie": received.document_serie,
                "rps_number": received.rps_number,
                "provider_cnpj": received.provider_cnpj,
                "provider_name": received.provider_name,
                "service_value": received.service_value,
                "service_description": received.service_description,
                "fiscal_additional_data": received.fiscal_additional_data,
                "issqn_base": received.issqn_base,
                "issqn_percent": received.issqn_percent,
                "issqn_value": received.issqn_value,
                "issqn_wh_percent": received.issqn_wh_percent,
                "issqn_wh_value": received.issqn_wh_value,
                "service_lc116_code": received.service_lc116_code,
                "service_nbs_code": received.service_nbs_code,
                "issqn_city_ibge": received.issqn_city_ibge,
                "civil_construction_code": received.civil_construction_code,
                "civil_construction_art": received.civil_construction_art,
                "partner_id": (
                    received.partner_id.id if received.partner_id else False
                ),
                "fiscal_operation_id": (default_op.id if default_op else False),
            }
        )

        service_type = self._resolve_service_type(received.service_lc116_code)
        nbs = self._resolve_nbs(received.service_nbs_code)
        product = self._resolve_service_product(service_type, nbs)
        if service_type:
            vals["service_type_id"] = service_type.id
        if nbs:
            vals["nbs_id"] = nbs.id
        if product:
            vals["product_id"] = product.id

        existing = self._find_existing_move(received)
        if existing:
            vals["account_move_id"] = existing.id

        return vals

    def action_import_document(self):
        """Create or link the vendor bill and mark the NFS-e as done."""
        self.ensure_one()
        if self.account_move_id:
            self.received_id.write(
                {
                    "account_move_id": self.account_move_id.id,
                    "document_id": (
                        self.account_move_id.fiscal_document_id.id or False
                    ),
                    "state": "done",
                }
            )
            return self._action_open_move(self.account_move_id)
        move = self._create_vendor_bill()
        self.received_id.write(
            {
                "account_move_id": move.id,
                "document_id": move.fiscal_document_id.id or False,
                "state": "done",
            }
        )
        return self._action_open_move(move)

    def action_view_existing_document(self):
        """Open the already-existing vendor bill."""
        self.ensure_one()
        if self.account_move_id:
            return self._action_open_move(self.account_move_id)

    def _create_vendor_bill(self):
        """Build and persist an account.move for the received NFS-e."""
        doc_type = self.env.ref("l10n_br_fiscal.document_SE", raise_if_not_found=False)

        partner = self.partner_id
        if not partner and self.provider_name:
            partner = self.env["res.partner"].create({"name": self.provider_name})

        fiscal_op = self.fiscal_operation_id or self._default_fiscal_operation()
        journal = self._get_purchase_journal()

        invoice_date = self.emission_date and self.emission_date.date() or False

        move_vals = {
            "move_type": "in_invoice",
            "company_id": self.company_id.id,
            "partner_id": partner.id if partner else False,
            "invoice_date": invoice_date,
            "document_type_id": doc_type.id if doc_type else False,
            "document_number": self.nfse_number,
            "document_serie": self.document_serie or False,
            "document_date": self.emission_date or False,
            "rps_number": self.rps_number or False,
            "fiscal_operation_id": fiscal_op.id if fiscal_op else False,
            "issuer": "partner",
            "imported_document": True,
        }
        if journal:
            move_vals["journal_id"] = journal.id
        if self.verify_code:
            move_vals["verify_code"] = self.verify_code
        if self.civil_construction_code:
            move_vals["civil_construction_code"] = self.civil_construction_code
        if self.civil_construction_art:
            move_vals["civil_construction_art"] = self.civil_construction_art
        if self.fiscal_additional_data:
            move_vals["fiscal_additional_data"] = self.fiscal_additional_data

        line_vals = self._build_invoice_line_vals(fiscal_op)
        move_vals["invoice_line_ids"] = [(0, 0, line_vals)]

        move = self.env["account.move"].create(move_vals)

        if self.received_id.attachment_id:
            self.received_id.attachment_id.write(
                {"res_model": "account.move", "res_id": move.id}
            )

        return move

    def _build_invoice_line_vals(self, fiscal_op):
        """Assemble invoice line values with all mapped NFS-e fiscal fields."""
        uom = self.env.ref("uom.product_uom_unit", raise_if_not_found=False)
        service_type = self.service_type_id or self._resolve_service_type(
            self.service_lc116_code
        )
        nbs = self.nbs_id or self._resolve_nbs(self.service_nbs_code)
        product = self.product_id or self._resolve_service_product(service_type, nbs)

        line_vals = {
            "name": self.service_description or "/",
            "price_unit": self.service_value or 0.0,
            "quantity": 1.0,
            "tax_icms_or_issqn": "issqn",
        }
        account = self._get_line_account(product)
        if account:
            line_vals["account_id"] = account.id
        if product:
            line_vals["product_id"] = product.id
        if uom:
            line_vals["product_uom_id"] = uom.id
        if fiscal_op:
            line_vals["fiscal_operation_id"] = fiscal_op.id
        if self.issqn_base:
            line_vals["issqn_base"] = self.issqn_base
        if self.issqn_percent:
            line_vals["issqn_percent"] = self.issqn_percent
        if self.issqn_value:
            line_vals["issqn_value"] = self.issqn_value
        if self.issqn_wh_percent:
            line_vals["issqn_wh_percent"] = self.issqn_wh_percent
        if self.issqn_wh_value:
            line_vals["issqn_wh_value"] = self.issqn_wh_value
        if service_type:
            line_vals["service_type_id"] = service_type.id
        if nbs:
            line_vals["nbs_id"] = nbs.id
        if self.issqn_city_ibge:
            city = self.env["res.city"].search(
                [("ibge_code", "=", self.issqn_city_ibge)], limit=1
            )
            if city:
                line_vals["issqn_fg_city_id"] = city.id
        return line_vals

    def _get_purchase_journal(self):
        """Return the purchase journal for the wizard's company."""
        return self.env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", self.company_id.id)],
            limit=1,
        )

    def _get_line_account(self, product):
        """Return the expense GL account for the invoice line."""
        if product:
            accounts = product.product_tmpl_id.get_product_accounts()
            account = accounts.get("expense")
            if account:
                return account
        return self.env["account.account"].search(
            [
                ("user_type_id.type", "in", ("expense", "other")),
                ("company_id", "=", self.company_id.id),
                ("deprecated", "=", False),
            ],
            limit=1,
        )

    def _resolve_service_product(self, service_type, nbs):
        """Find a matching service product; create one if not found."""
        Product = self.env["product.product"]
        base_domain = [("type", "in", ("service", "consu"))]
        for field, record in (
            ("service_type_id", service_type),
            ("nbs_id", nbs),
        ):
            if not record:
                continue
            tmpl = self.env["product.template"].search(
                base_domain + [(field, "=", record.id)], limit=1
            )
            if tmpl:
                return tmpl.product_variant_ids[:1] or Product.browse()

        name = (
            (service_type and service_type.name)
            or (nbs and nbs.name)
            or (self.service_description or "")[:80]
            or self.provider_name
            or "Serviço NFS-e"
        )
        uom = self.env.ref("uom.product_uom_unit", raise_if_not_found=False)
        ncm_service = self.env.ref(
            "l10n_br_fiscal.ncm_00000000", raise_if_not_found=False
        )
        tmpl_vals = {
            "name": name,
            "type": "service",
            "invoice_policy": "delivery",
            "tax_icms_or_issqn": "issqn",
            "fiscal_type": "09",
            "icms_origin": "0",
        }
        if uom:
            tmpl_vals["uom_id"] = uom.id
            tmpl_vals["uom_po_id"] = uom.id
        if ncm_service:
            tmpl_vals["ncm_id"] = ncm_service.id
        if service_type:
            tmpl_vals["service_type_id"] = service_type.id
        if nbs:
            tmpl_vals["nbs_id"] = nbs.id
        tmpl = self.env["product.template"].create(tmpl_vals)
        return tmpl.product_variant_ids[:1] or Product.browse()

    def _resolve_service_type(self, raw_code):
        """Resolve a 6-digit cTribNac code to a service type record."""
        ServiceType = self.env["l10n_br_fiscal.service.type"]
        if not raw_code:
            return ServiceType.browse()
        digits = "".join(c for c in raw_code if c.isdigit())
        if len(digits) < 2:
            return ServiceType.browse()
        pairs = [digits[i : i + 2] for i in range(0, min(len(digits), 6), 2)]
        section = str(int(pairs[0]))
        candidates = []
        for depth in range(len(pairs), 0, -1):
            if depth == 1:
                candidates.append(section)
            else:
                candidates.append(f"{section}.{'.'.join(pairs[1:depth])}")
        for code in candidates:
            rec = ServiceType.search([("code", "=", code)], limit=1)
            if rec:
                return rec
        return ServiceType.browse()

    def _resolve_nbs(self, digits_only):
        """Resolve a digits-only NBS code to an l10n_br_fiscal.nbs record."""
        Nbs = self.env["l10n_br_fiscal.nbs"]
        if not digits_only:
            return Nbs.browse()
        all_nbs = Nbs.search([])
        exact = all_nbs.filtered(lambda r: r.code.replace(".", "") == digits_only)
        if exact:
            return exact[:1]
        for prefix_len in (6, 5):
            prefix = digits_only[:prefix_len]
            match = all_nbs.filtered(
                lambda r, p=prefix: r.code.replace(".", "").startswith(p)
            )
            if match:
                return match[:1]
        return Nbs.browse()

    def _default_fiscal_operation(self):
        """Return the first approved inbound fiscal operation."""
        return self.env["l10n_br_fiscal.operation"].search(
            [("fiscal_operation_type", "=", "in"), ("state", "=", "approved")],
            limit=1,
        )

    @staticmethod
    def _find_existing_move(received):
        """Return an existing vendor bill matching this NFS-e, if any."""
        env = received.env
        doc_type = env.ref("l10n_br_fiscal.document_SE", raise_if_not_found=False)
        if not received.nfse_number:
            return env["account.move"].browse()
        domain = [
            ("move_type", "=", "in_invoice"),
            ("document_number", "=", received.nfse_number),
        ]
        if doc_type:
            domain.append(("document_type_id", "=", doc_type.id))
        if received.provider_cnpj:
            digits = "".join(c for c in received.provider_cnpj if c.isdigit())
            if digits:
                domain.append(("partner_id.cnpj_cpf", "like", digits[-11:]))
        return env["account.move"].search(domain, limit=1)

    @staticmethod
    def _action_open_move(move):
        return {
            "type": "ir.actions.act_window",
            "name": _("Vendor Bill"),
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
            "target": "current",
        }
