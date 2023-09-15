# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm
from nfelib.mdfe.bindings.v3_0.mdfe_modal_rodoviario_v3_00 import Rodo

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeModalRodoviario(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario"
    _inherit = "mdfe.30.rodo"
    _mdfe_search_keys = ["mdfe30_codAgPorto"]

    mdfe30_infANTT = fields.Many2one(comodel_name="l10n_br_mdfe.modal.rodoviario.antt")

    mdfe30_veicTracao = fields.Many2one(
        comodel_name="l10n_br_mdfe.modal.rodoviario.veiculo.tracao", required=True
    )

    mdfe30_veicReboque = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.reboque"
    )

    mdfe30_lacRodo = fields.One2many(comodel_name="l10n_br_mdfe.transporte.lacre")


class MDFeModalRodoviarioANTT(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.antt"
    _inherit = "mdfe.30.infantt"
    _mdfe_search_keys = ["mdfe30_RNTRC"]

    mdfe30_infCIOT = fields.One2many(comodel_name="l10n_br_mdfe.modal.rodoviario.ciot")

    mdfe30_valePed = fields.Many2one(
        comodel_name="l10n_br_mdfe.modal.rodoviario.vale_pedagio"
    )

    mdfe30_infContratante = fields.One2many(comodel_name="res.partner")

    mdfe30_infPag = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.pagamento"
    )


class MDFeModalRodoviarioCIOT(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.ciot"
    _inherit = "mdfe.30.infciot"
    _mdfe_search_keys = ["mdfe30_CIOT"]

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_CIOT = fields.Char(required=True)

    is_company = fields.Boolean(string="É empresa?", required=True)

    mdfe30_CNPJ = fields.Char(string="CNPJ do responsável")

    mdfe30_CPF = fields.Char(string="CPF do responsável")

    mdfe30_choice1 = fields.Selection(
        selection=[("mdfe30_CNPJ", "CNPJ"), ("mdfe30_CPF", "CPF")],
        string="CNPJ/CPF do responsável",
        compute="_compute_ciot_choice",
    )

    @api.depends("is_company")
    def _compute_ciot_choice(self):
        for record in self:
            record.mdfe30_choice1 = "mdfe30_CNPJ" if record.is_company else "mdfe30_CPF"

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        cnpj_cpf_data = {}
        if self.is_company:
            cnpj_cpf_data["CNPJ"] = self.mdfe30_CNPJ
        else:
            cnpj_cpf_data["CPF"] = self.mdfe30_CPF

        return Rodo.InfAntt.InfCiot(CIOT=self.mdfe30_CIOT, **cnpj_cpf_data)

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class MDFeModalRodoviarioValePedagio(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.vale_pedagio"
    _inherit = "mdfe.30.valeped"

    mdfe30_disp = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.vale_pedagio.dispositivo"
    )


class MDFeModalRodoviarioValePedagioDispositivo(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.vale_pedagio.dispositivo"
    _inherit = "mdfe.30.disp"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_CNPJForn = fields.Char(required=True)

    mdfe30_vValePed = fields.Monetary(required=True)

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        optional_data = {}
        if self.mdfe30_CNPJPg:
            optional_data["CNPJPg"] = self.mdfe30_CNPJPg

        if self.mdfe30_CPFPg:
            optional_data["CPFPg"] = self.mdfe30_CPFPg

        if self.mdfe30_nCompra:
            optional_data["nCompra"] = self.mdfe30_nCompra

        if self.mdfe30_tpValePed:
            optional_data["tpValePed"] = self.mdfe30_tpValePed

        return Rodo.InfAntt.ValePed.Disp(
            CNPJForn=self.mdfe30_CNPJForn,
            vValePed=self.mdfe30_vValePed,
            **optional_data,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class MDFeModalRodoviarioPagamento(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.pagamento"
    _inherit = "mdfe.30.rodo_infpag"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Responsável pelo pagamento", required=True
    )

    mdfe30_CNPJ = fields.Char(related="partner_id.mdfe30_CNPJ")

    mdfe30_CPF = fields.Char(related="partner_id.mdfe30_CPF")

    mdfe30_xNome = fields.Char(related="partner_id.mdfe30_xNome")

    mdfe30_choice1 = fields.Selection(
        selection=[
            ("mdfe30_CNPJ", "CNPJ"),
            ("mdfe30_CPF", "CPF"),
            ("mdfe40_idEstrangeiro", "idEstrangeiro"),
        ],
        string="CNPJ/CPF/Id Estrangeiro do responsável pelo pagamento",
        compute="_compute_mdfe_data",
    )

    mdfe30_comp = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.pagamento.frete"
    )

    mdfe30_infPrazo = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.pagamento.prazo"
    )

    mdfe30_vContrato = fields.Monetary(required=True)

    mdfe30_indPag = fields.Selection(required=True)

    mdfe30_infBanc = fields.Many2one(
        comodel_name="l10n_br_mdfe.modal.rodoviario.pagamento.banco", required=True
    )

    @api.depends("partner_id")
    def _compute_mdfe_data(self):
        for rec in self:
            cnpj_cpf = punctuation_rm(rec.partner_id.cnpj_cpf)
            if cnpj_cpf:
                if rec.partner_id.country_id.code != "BR":
                    rec.mdfe30_choice1 = "mdfe40_idEstrangeiro"
                elif rec.partner_id.is_company:
                    rec.mdfe30_choice1 = "mdfe30_CNPJ"
                else:
                    rec.mdfe30_choice1 = "mdfe30_CPF"
            else:
                rec.mdfe30_choice1 = False

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        additional_data = {}
        if self.mdfe30_choice1 == "mdfe30_idEstrangeiro":
            additional_data["idEstrangeiro"] = self.mdfe30_idEstrangeiro
        elif self.mdfe30_choice1 == "mdfe30_CNPJ":
            additional_data["CNPJ"] = self.mdfe30_CNPJ
        else:
            additional_data["CPF"] = self.mdfe30_CPF

        if self.mdfe30_infPrazo:
            additional_data["infPrazo"] = self.mdfe30_infPrazo.export_fields()

        if self.mdfe30_comp:
            additional_data["comp"] = self.mdfe30_comp.export_fields()

        if self.mdfe30_indAltoDesemp:
            additional_data["indAltoDesemp"] = self.mdfe30_indAltoDesemp

        if self.mdfe30_vAdiant:
            additional_data["vAdiant"] = self.mdfe30_vAdiant

        if self.mdfe30_xNome:
            additional_data["xNome"] = self.mdfe30_xNome

        return Rodo.InfAntt.InfPag(
            vContrato=self.mdfe30_vContrato,
            indPag=self.mdfe30_indPag,
            infBanc=self.mdfe30_infBanc.export_fields(),
            **additional_data,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class MDFeModalRodoviarioPagamentoBanco(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.pagamento.banco"
    _inherit = "mdfe.30.rodo_infbanc"

    payment_type = fields.Selection(
        selection=[
            ("bank", "Banco"),
            ("pix", "PIX"),
        ],
        string="Meio de Pagamento",
        default="bank",
    )

    mdfe30_choice1 = fields.Selection(
        selection=[
            ("mdfe30_codBanco", "Banco"),
            ("mdfe30_codAgencia", "Agencia"),
            ("mdfe30_CNPJIPEF", "CNPJ"),
            ("mdfe30_PIX", "PIX"),
        ],
        string="Método de Pagamento",
        compute="_compute_payment_type",
    )

    @api.depends("payment_type")
    def _compute_payment_type(self):
        for record in self:
            if record.payment_type == "bank":
                record.mdfe30_choice1 = "mdfe30_codBanco"
            elif record.payment_type == "pix":
                record.mdfe30_choice1 = "mdfe30_PIX"
            else:
                record.mdfe30_choice1 = False

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        bank_data = {}
        if self.mdfe30_choice1 == "mdfe30_codBanco":
            bank_data["codBanco"] = self.mdfe30_codBanco
            bank_data["codAgencia"] = self.mdfe30_codAgencia
        elif self.mdfe30_choice1 == "mdfe30_PIX":
            bank_data["PIX"] = self.mdfe30_PIX

        return Rodo.InfAntt.InfPag.InfBanc(**bank_data)

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class MDFeModalRodoviarioPagamentoFrete(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.pagamento.frete"
    _inherit = "mdfe.30.rodo_comp"

    mdfe30_tpComp = fields.Selection(required=True)

    mdfe30_vComp = fields.Monetary(required=True)

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        optional_data = {}
        if self.mdfe30_vComp:
            optional_data["xComp"] = self.mdfe30_vComp

        return Rodo.InfAntt.InfPag.Comp(
            tpComp=self.mdfe30_tpComp, vComp=self.mdfe30_vComp, **optional_data
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class MDFeModalRodoviarioPagamentoPrazo(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.pagamento.prazo"
    _inherit = "mdfe.30.rodo_infprazo"

    mdfe30_nParcela = fields.Char(required=True)

    mdfe30_dVenc = fields.Date(required=True)

    mdfe30_vParcela = fields.Monetary(required=True)

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        return Rodo.InfAntt.InfPag.InfPrazo(
            nParcela=self.mdfe30_nParcela,
            dVenc=self.mdfe30_dVenc,
            vParcela=self.mdfe30_vParcela,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class MDFeModalRodoviarioVeiculoTracao(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.veiculo.tracao"
    _inherit = "mdfe.30.veictracao"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_prop = fields.Many2one(comodel_name="res.partner")

    mdfe30_condutor = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.veiculo.condutor"
    )

    mdfe30_placa = fields.Char(required=True)

    mdfe30_tara = fields.Char(required=True)

    mdfe30_capKG = fields.Char(required=True)

    mdfe30_tpRod = fields.Selection(required=True)

    mdfe30_tpCar = fields.Selection(required=True)


class MDFeModalRodoviarioVeiculoCondutor(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.veiculo.condutor"
    _inherit = "mdfe.30.rodo_condutor"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_xNome = fields.Char(required=True)

    mdfe30_CPF = fields.Char(required=True)

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        return Rodo.VeicTracao.Condutor(xNome=self.mdfe30_xNome, CPF=self.mdfe30_CPF)

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class MDFeModalRodoviarioReboque(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.reboque"
    _inherit = "mdfe.30.veicreboque"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_prop = fields.Many2one(comodel_name="res.partner")

    mdfe30_placa = fields.Char(required=True)

    mdfe30_tara = fields.Char(required=True)

    mdfe30_capKG = fields.Char(required=True)

    mdfe30_tpCar = fields.Selection(required=True)

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        optional_data = {}
        if self.mdfe30_cInt:
            optional_data["cInt"] = self.mdfe30_cInt

        if self.mdfe30_RENAVAM:
            optional_data["RENAVAM"] = self.mdfe30_RENAVAM

        if self.mdfe30_capKG:
            optional_data["capKG"] = self.mdfe30_capKG

        if self.mdfe30_capM3:
            optional_data["capM3"] = self.mdfe30_capM3

        if self.mdfe30_prop:
            optional_data["prop"] = self.mdfe30_prop.export_proprietary_fields(
                Rodo.VeicReboque.Prop
            )

        if self.mdfe30_UF:
            optional_data["UF"] = self.mdfe30_UF

        return Rodo.VeicReboque(
            placa=self.mdfe30_placa,
            tara=self.mdfe30_tara,
            tpCar=self.mdfe30_tpCar,
            **optional_data,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]
