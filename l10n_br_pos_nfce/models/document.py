# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base.misc import punctuation_rm

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    PROCESSADOR_OCA,
)


def filter_processador_edoc_nfe(record):
    if record.processador_edoc == PROCESSADOR_OCA and record.document_type_id.code in [
        MODELO_FISCAL_NFE,
        MODELO_FISCAL_NFCE,
    ]:
        return True
    return False


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if (
            field_name == "nfe40_dest"
            and ((self.has_vat_specification) or (self.partner_id.vat))
            and self.document_type == MODELO_FISCAL_NFCE
        ):
            return self._setup_minimal_dest(field_name, xsd_required, class_obj)
        if (
            field_name == "nfe40_dest"
            and (not self.has_vat_specification)
            and (not self.partner_id.vat)
            and self.document_type == MODELO_FISCAL_NFCE
        ):
            return self._setup_no_dest(field_name, xsd_required, class_obj)

        return super()._export_many2one(field_name, xsd_required, class_obj)

    def _setup_minimal_dest(self, field_name, xsd_required, class_obj):
        """
        Minimal setup dest  for cases with VAT specification
        commonly known as 'CPF na nota'.
        """
        res = super()._export_many2one(field_name, xsd_required, class_obj)
        if (self.partner_cnpj_cpf and len(self.partner_cnpj_cpf) <= 11) or (
            self.partner_id.vat and len(punctuation_rm(self.partner_id.vat)) <= 11
        ):
            # CPF
            res.CPF = self.partner_cnpj_cpf or punctuation_rm(self.partner_id.vat)
            res.CNPJ = None
        else:
            # CNPJ
            res.CNPJ = self.partner_cnpj_cpf
            res.CPF = None
        # Remove every non-used attribute for VAT in NF case
        res.enderDest = None
        res.CEP = None
        res.xNome = None
        return res

    def _setup_no_dest(self, field_name, xsd_required, class_obj):
        """
        Setup dest for cases without VAT specification and anonymous consumer.
        """
        return None

    def _serialize(self, edocs):
        for record in self.with_context(lang="pt_BR").filtered(
            filter_processador_edoc_nfe
        ):
            if record.document_type == MODELO_FISCAL_NFCE:
                record._document_qrcode()

        edocs = super()._serialize(edocs)

        for record in self.with_context(lang="pt_BR").filtered(
            filter_processador_edoc_nfe
        ):
            processor = record.processador_edoc

            record.flush()
            record.invalidate_cache()

            inf_nfe = record._build_binding("nfe", "40")

            if hasattr(record, "move_ids") and record.move_ids:
                record.move_ids.processador_edoc = processor

            record.processador_edoc = processor

            inf_nfe_supl = None

            if record.nfe40_infNFeSupl:
                inf_nfe_supl = record.nfe40_infNFeSupl._build_binding("nfe", "40")

            if record.document_type == MODELO_FISCAL_NFCE:
                if hasattr(inf_nfe.dest, "enderDest"):
                    del inf_nfe.dest.enderDest

            for nfe in edocs:
                if nfe.infNFe.ide.nNF == inf_nfe.ide.nNF:
                    nfe.infNFe = inf_nfe
                    nfe.infNFeSupl = inf_nfe_supl

                    # NFC-e em homologação (fix, antes nao tinha esse patch)
                    if (
                        record.document_type == MODELO_FISCAL_NFCE
                        and nfe.infNFe.ide.tpAmb == "2"
                        and nfe.infNFe.det
                    ):
                        nfe.infNFe.det[0].prod.xProd = (
                            "NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO "
                            "- SEM VALOR FISCAL"
                        )

                    break

        return edocs

    def _prepare_nfce_send(self):
        self.ensure_one()
        # self._prepare_payments_for_nfce()
        # self.nfe40_infNFeSupl = self.env["l10n_br_fiscal.document.supplement"].create(
        #    {
        #        "nfe40_qrCode": self.get_nfce_qrcode(),
        #        "nfe40_urlChave": self.get_nfce_qrcode_url(),
        #    }
        # )
        self.nfe40_detPag.filtered(lambda p: p.nfe40_tPag == "99").write(
            {"nfe40_xPag": "Outros"}
        )

    def _document_qrcode(self):
        super()._document_qrcode()

        for record in self.filtered(lambda d: d.document_type == MODELO_FISCAL_NFCE):
            if record.nfe40_infNFeSupl:
                record.nfe40_infNFeSupl.unlink()
            record.nfe40_infNFeSupl = self.env[
                "l10n_br_fiscal.document.supplement"
            ].create(
                {
                    "qrcode": record.get_nfce_qrcode(),
                    "url_key": record.get_nfce_qrcode_url(),
                }
            )