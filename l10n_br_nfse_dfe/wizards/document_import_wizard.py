# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from erpbrasil.base.fiscal.cnpj_cpf import formata

from odoo import Command, _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_PARTNER,
    FISCAL_IN,
    FISCAL_OUT,
    TAX_BASE_TYPE_PERCENT,
    TAX_DOMAIN_ISSQN,
)
from odoo.addons.l10n_br_fiscal_dfe.tools import utils

from ..constants.nfse_dfe import NFSE_ACCESS_KEY_SIZE
from ..services.nfse_xml import parse_nfse_file


class DocumentImportWizard(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.import.wizard"

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Service Product",
        domain="[('type', '=', 'service')]",
    )

    def _parse_file(self):
        binding = parse_nfse_file(self.file)
        if binding:
            return binding
        return super()._parse_file()

    def _detect_binding(self, binding):
        if getattr(binding, "is_national_nfse", False):
            self._detect_document_type("SE")
            return
        return super()._detect_binding(binding)

    def _extract_binding_data(self, binding):
        if not getattr(binding, "is_national_nfse", False):
            return super()._extract_binding_data(binding)
        provider = binding.provider or {}
        provider_digits = (
            provider.get("cnpj") or provider.get("cpf") or binding.provider_cnpj
        )
        self.document_key = binding.access_key
        self.document_number = (binding.number or "").lstrip("0") or binding.number
        self.document_serie = binding.serie
        self.issuer_legal_name = provider.get("legal_name") or binding.provider_name
        self.issuer_cnpj = formata(provider_digits) if provider_digits else False
        self.issuer_partner_id = (
            self._search_partner(cnpj=provider_digits) if provider_digits else False
        )
        self.partner_id = self.issuer_partner_id
        if not self.product_id and self.company_id.nfse_import_product_id:
            self.product_id = self.company_id.nfse_import_product_id
        self.issuer_type_in_out = FISCAL_OUT
        self.rps_number = binding.rps_number
        company_digits = re.sub(r"\D", "", self.company_id.vat or "")
        self.destination_cnpj = (
            utils.mask_cnpj(company_digits) if company_digits else False
        )
        self.destination_partner_id = self.company_id.partner_id
        self.destination_type_in_out = FISCAL_IN
        self.fiscal_operation_id = self._nfse_default_operation()

    def _nfse_default_operation(self):
        operation = self.env.ref("l10n_br_fiscal.fo_compras", raise_if_not_found=False)
        if operation and operation.fiscal_operation_type == "in":
            return operation
        return self.env["l10n_br_fiscal.operation"].search(
            [("fiscal_operation_type", "=", "in"), ("state", "=", "approved")],
            limit=1,
        )

    def _create_edoc_from_file(self):
        binding = self._parse_file()
        if not getattr(binding, "is_national_nfse", False):
            return super()._create_edoc_from_file()
        if not binding.access_key or len(binding.access_key) != NFSE_ACCESS_KEY_SIZE:
            raise UserError(_("The NFS-e XML does not contain a 50-digit access key."))
        partner = self.partner_id or self.issuer_partner_id
        provider = binding.provider or {}
        provider_digits = (
            provider.get("cnpj") or provider.get("cpf") or binding.provider_cnpj
        )
        if not partner and provider_digits:
            partner = self._search_partner(cnpj=provider_digits)
        if not partner:
            partner = self._nfse_create_provider_partner(binding)
        document = self.env["l10n_br_fiscal.document"].create(
            self._nfse_document_vals(binding, partner)
        )
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "product_id": self.product_id.id if self.product_id else False,
                "quantity": 1.0,
                "fiscal_operation_id": self.fiscal_operation_id.id,
            }
        )
        line.write(self._nfse_line_vals(binding))
        self.env["ir.attachment"].create(
            {
                "name": f"NFSe-{binding.access_key}.xml",
                "datas": self.file,
                "res_model": document._name,
                "res_id": document.id,
            }
        )
        if not self.partner_id:
            self.partner_id = document.partner_id
        self.document_id = document
        return binding, document

    def _nfse_create_provider_partner(self, binding):
        """Create the provider partner. Never called from the onchange."""
        provider = binding.provider or {}
        digits = re.sub(
            r"\D",
            "",
            provider.get("cnpj") or provider.get("cpf") or binding.provider_cnpj or "",
        )
        if len(digits) not in (11, 14):
            return self.env["res.partner"]
        city = self.env["res.city"]
        if provider.get("city_ibge"):
            city = self.env["res.city"].search(
                [("ibge_code", "=", provider["city_ibge"])], limit=1
            )
        name = provider.get("name") or provider.get("legal_name") or formata(digits)
        vals = {
            "name": name,
            "legal_name": provider.get("legal_name") or name,
            "vat": formata(digits),
            "is_company": len(digits) == 14,
            "company_type": "company" if len(digits) == 14 else "person",
            "country_id": self.env.ref("base.br").id,
        }
        if provider.get("im"):
            vals["l10n_br_im_code"] = provider["im"]
        if provider.get("phone"):
            vals["phone"] = provider["phone"]
        if provider.get("email"):
            vals["email"] = provider["email"]
        if provider.get("street_name"):
            vals["street_name"] = provider["street_name"]
        if provider.get("street_number"):
            vals["street_number"] = provider["street_number"]
        if provider.get("street2"):
            vals["street2"] = provider["street2"]
        if provider.get("district"):
            vals["district"] = provider["district"]
        if provider.get("zip"):
            vals["zip"] = provider["zip"]
        if city:
            vals["city_id"] = city.id
            vals["state_id"] = city.state_id.id
        return self.env["res.partner"].create(vals)

    def _nfse_document_vals(self, binding, partner):
        number = (binding.number or "").lstrip("0") or binding.number
        return {
            "company_id": self.company_id.id,
            "partner_id": partner.id if partner else False,
            "issuer": DOCUMENT_ISSUER_PARTNER,
            "imported_document": True,
            "document_type_id": self.env.ref("l10n_br_fiscal.document_SE").id,
            "fiscal_operation_id": self.fiscal_operation_id.id,
            "document_key": binding.access_key,
            "document_number": number,
            "document_serie": binding.serie,
            "document_date": binding.emission_date or fields.Datetime.now(),
            "rps_number": binding.rps_number,
        }

    def _nfse_line_vals(self, binding):
        service_type = self._nfse_find_service_type(binding.service_lc116_code)
        nbs = self._nfse_find_nbs(binding.service_nbs_code)
        vals = {
            "name": binding.description or _("Service"),
            "price_unit": binding.service_value,
            "tax_icms_or_issqn": TAX_DOMAIN_ISSQN,
            "service_type_id": service_type.id if service_type else False,
            "nbs_id": nbs.id if nbs else False,
            "issqn_base": binding.issqn_base or binding.service_value,
            "issqn_percent": binding.issqn_percent,
            "issqn_value": binding.issqn_value,
            "issqn_wh_percent": binding.issqn_wh_percent,
            "issqn_wh_value": binding.issqn_wh_value,
            "issqn_fg_city_id": self._nfse_incidence_city(binding.issqn_city_ibge).id,
        }
        vals.update(self._nfse_tax_vals(binding))
        return vals

    def _nfse_incidence_city(self, ibge_code):
        digits = re.sub(r"\D", "", ibge_code or "")
        if not digits:
            return self.env["res.city"].browse()
        return self.env["res.city"].search([("ibge_code", "=", digits)], limit=1)

    def _nfse_tax_vals(self, binding):
        """Copy ISS, IBS, CBS and federal taxes from the national XML.

        The document is imported, so the fiscal computes do not replace these
        amounts. The service liquid value stays the one parsed as price.
        """
        vals = {}
        tax_ids = []
        vals.update(self._nfse_issqn_vals(binding, tax_ids))
        vals.update(self._nfse_ibs_cbs_vals(binding, tax_ids))
        vals.update(self._nfse_pis_cofins_vals(binding, tax_ids))
        vals.update(self._nfse_withholding_vals(binding, tax_ids))
        if tax_ids:
            vals["fiscal_tax_ids"] = [Command.set(tax_ids)]
        return vals

    def _nfse_issqn_vals(self, binding, tax_ids):
        """Match the chart ISS by rate. Withholding uses the retained group."""
        base = binding.issqn_base or binding.service_value
        issqn_tax = self._nfse_match_tax(
            "l10n_br_fiscal.tax_group_issqn",
            binding.issqn_percent,
        )
        vals = self._nfse_amount_vals(
            "issqn",
            base,
            binding.issqn_percent,
            binding.issqn_value,
            0.0,
            False,
            issqn_tax,
        )
        if issqn_tax:
            tax_ids.append(issqn_tax.id)
        if not binding.issqn_wh_value:
            return vals
        wh_tax = self._nfse_match_tax(
            "l10n_br_fiscal.tax_group_issqn_wh",
            binding.issqn_wh_percent or binding.issqn_percent,
        )
        vals.update(
            self._nfse_amount_vals(
                "issqn_wh",
                base,
                binding.issqn_wh_percent or binding.issqn_percent,
                binding.issqn_wh_value,
                0.0,
                False,
                wh_tax,
            )
        )
        if wh_tax:
            tax_ids.append(wh_tax.id)
        return vals

    def _nfse_ibs_cbs_vals(self, binding, tax_ids):
        classification = self._nfse_tax_classification(binding.tax_classification_code)
        cst = self._nfse_cst("ibs", binding.ibs_cbs_cst)
        cbs_cst = self._nfse_cst("cbs", binding.ibs_cbs_cst)
        ibs_tax = classification.tax_ibs_id or self._nfse_match_tax(
            "l10n_br_fiscal.tax_group_ibs",
            binding.ibs_percent,
            binding.ibs_reduction,
            cst,
        )
        cbs_tax = classification.tax_cbs_id or self._nfse_match_tax(
            "l10n_br_fiscal.tax_group_cbs",
            binding.cbs_percent,
            binding.cbs_reduction,
            cbs_cst,
        )
        vals = self._nfse_amount_vals(
            "ibs",
            binding.ibs_base,
            binding.ibs_percent,
            binding.ibs_value,
            binding.ibs_reduction,
            cst,
            ibs_tax,
        )
        vals.update(
            self._nfse_amount_vals(
                "cbs",
                binding.cbs_base,
                binding.cbs_percent,
                binding.cbs_value,
                binding.cbs_reduction,
                cbs_cst,
                cbs_tax,
            )
        )
        if classification:
            vals["tax_classification_id"] = classification.id
        for tax in (ibs_tax, cbs_tax):
            if tax:
                tax_ids.append(tax.id)
        return vals

    def _nfse_pis_cofins_vals(self, binding, tax_ids):
        pis_cst = self._nfse_cst("pis", binding.pis_cofins_cst)
        cofins_cst = self._nfse_cst("cofins", binding.pis_cofins_cst)
        pis_tax = self._nfse_match_tax(
            "l10n_br_fiscal.tax_group_pis",
            binding.pis_percent,
            0.0,
            pis_cst,
        )
        cofins_tax = self._nfse_match_tax(
            "l10n_br_fiscal.tax_group_cofins",
            binding.cofins_percent,
            0.0,
            cofins_cst,
        )
        vals = self._nfse_amount_vals(
            "pis",
            binding.pis_cofins_base,
            binding.pis_percent,
            binding.pis_value,
            0.0,
            pis_cst,
            pis_tax,
        )
        vals.update(
            self._nfse_amount_vals(
                "cofins",
                binding.pis_cofins_base,
                binding.cofins_percent,
                binding.cofins_value,
                0.0,
                cofins_cst,
                cofins_tax,
            )
        )
        if binding.pis_withheld:
            vals.update(
                self._nfse_amount_vals(
                    "pis_wh",
                    binding.pis_cofins_base,
                    binding.pis_percent,
                    binding.pis_value,
                    0.0,
                    False,
                    self.env["l10n_br_fiscal.tax"].browse(),
                )
            )
        if binding.cofins_withheld:
            vals.update(
                self._nfse_amount_vals(
                    "cofins_wh",
                    binding.pis_cofins_base,
                    binding.cofins_percent,
                    binding.cofins_value,
                    0.0,
                    False,
                    self.env["l10n_br_fiscal.tax"].browse(),
                )
            )
        for tax in (pis_tax, cofins_tax):
            if tax:
                tax_ids.append(tax.id)
        return vals

    def _nfse_withholding_vals(self, binding, tax_ids):
        """IRRF and CSLL come only as retained amounts."""
        base = binding.pis_cofins_base or binding.service_value
        vals = {}
        for prefix, group_xmlid, value in (
            ("irpj_wh", "l10n_br_fiscal.tax_group_irpj_wh", binding.irpj_wh_value),
            ("csll_wh", "l10n_br_fiscal.tax_group_csll_wh", binding.csll_wh_value),
        ):
            if not value:
                continue
            percent = self._nfse_percent(base, value)
            tax = self._nfse_match_tax(group_xmlid, percent) if percent else False
            vals.update(
                self._nfse_amount_vals(prefix, base, percent, value, 0.0, False, tax)
            )
            if tax:
                tax_ids.append(tax.id)
        return vals

    def _nfse_amount_vals(self, prefix, base, percent, value, reduction, cst, tax):
        if not any((base, percent, value, reduction, cst, tax)):
            return {}
        line_fields = self.env["l10n_br_fiscal.document.line"]._fields
        candidates = {
            f"{prefix}_base": base or 0.0,
            f"{prefix}_percent": percent or 0.0,
            f"{prefix}_value": value or 0.0,
            f"{prefix}_reduction": reduction or 0.0,
            f"{prefix}_base_type": TAX_BASE_TYPE_PERCENT,
        }
        if cst:
            candidates[f"{prefix}_cst_id"] = cst.id
        if tax:
            candidates[f"{prefix}_tax_id"] = tax.id
        return {key: item for key, item in candidates.items() if key in line_fields}

    @staticmethod
    def _nfse_percent(base, value):
        if not base or not value:
            return 0.0
        percent = round(value * 100.0 / base, 2)
        if round(base * percent / 100.0, 2) == round(value, 2):
            return percent
        return 0.0

    def _nfse_cst(self, kind, code):
        if not code:
            return self.env["l10n_br_fiscal.cst"].browse()
        found = self.env.ref(
            f"l10n_br_fiscal.cst_{kind}_{str(code).strip()}",
            raise_if_not_found=False,
        )
        return found or self.env["l10n_br_fiscal.cst"].browse()

    def _nfse_tax_classification(self, code):
        if not code:
            return self.env["l10n_br_fiscal.tax.classification"].browse()
        return self.env["l10n_br_fiscal.tax.classification"].search(
            [("code", "=", str(code).strip())],
            limit=1,
        )

    def _nfse_match_tax(self, group_xmlid, percent, reduction=0.0, cst=None):
        group = self.env.ref(group_xmlid, raise_if_not_found=False)
        if not group or not percent:
            return self.env["l10n_br_fiscal.tax"].browse()
        domain = [
            ("tax_group_id", "=", group.id),
            ("percent_amount", "=", percent),
            ("percent_reduction", "=", reduction or 0.0),
        ]
        tax_model = self.env["l10n_br_fiscal.tax"]
        if cst:
            found = tax_model.search(
                domain + ["|", ("cst_in_id", "=", cst.id), ("cst_out_id", "=", cst.id)],
                limit=1,
            )
            if found:
                return found
        return tax_model.search(domain, limit=1)

    def _nfse_find_service_type(self, code):
        service_model = self.env["l10n_br_fiscal.service.type"]
        digits = re.sub(r"\D", "", code or "")
        if len(digits) != 6:
            return service_model.browse()
        section = str(int(digits[0:2]))
        candidates = [
            f"{section}.{digits[2:4]}.{digits[4:6]}",
            f"{section}.{digits[2:4]}",
            section,
        ]
        for candidate in candidates:
            found = service_model.search(
                [("code", "=", candidate), ("internal_type", "=", "normal")],
                limit=1,
            )
            if found:
                return found
        return service_model.browse()

    def _nfse_find_nbs(self, code):
        digits = re.sub(r"\D", "", code or "")
        if not digits:
            return self.env["l10n_br_fiscal.nbs"].browse()
        return self.env["l10n_br_fiscal.nbs"].search(
            ["|", ("code_unmasked", "=", digits), ("code", "=", digits)],
            limit=1,
        )
