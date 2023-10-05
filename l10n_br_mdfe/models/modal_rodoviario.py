# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeModalRodoviario(spec_models.StackedModel):
    _name = "l10n_br_mdfe.modal.rodoviario"
    _inherit = "mdfe.30.rodo"
    _stacked = "mdfe.30.rodo"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_rodoviario_v3_00"
    _field_prefix = "mdfe30_"
    _schema_name = "mdfe"
    _schema_version = "3.0.0"
    _odoo_module = "l10n_br_mdfe"
    _spec_module = (
        "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_modal_rodoviario_v3_00"
    )
    _spec_tab_name = "MDFe"
    _description = "Modal Rodoviário MDFe"

    # all m2o at this level will be stacked even if not required:
    _force_stack_paths = ["rodo.infANTT", "rodo.infANTT.ValePed"]

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_codAgPorto = fields.Char(related="document_id.mdfe30_codAgPorto")

    mdfe30_infCIOT = fields.One2many(related="document_id.mdfe30_infCIOT")

    mdfe30_disp = fields.One2many(related="document_id.mdfe30_disp")

    mdfe30_categCombVeic = fields.Selection(related="document_id.mdfe30_categCombVeic")

    mdfe30_infContratante = fields.One2many(compute="_compute_contractor")

    mdfe30_RNTRC = fields.Char(related="document_id.mdfe30_RNTRC")

    mdfe30_infPag = fields.One2many(related="document_id.mdfe30_infPag")

    mdfe30_prop = fields.Many2one(related="document_id.mdfe30_prop")

    mdfe30_condutor = fields.One2many(related="document_id.mdfe30_condutor")

    mdfe30_cInt = fields.Char(related="document_id.mdfe30_cInt")

    mdfe30_RENAVAM = fields.Char(related="document_id.mdfe30_RENAVAM")

    mdfe30_placa = fields.Char(related="document_id.mdfe30_placa")

    mdfe30_tara = fields.Char(related="document_id.mdfe30_tara")

    mdfe30_capKG = fields.Char(related="document_id.mdfe30_capKG")

    mdfe30_capM3 = fields.Char(related="document_id.mdfe30_capM3")

    mdfe30_tpRod = fields.Selection(related="document_id.mdfe30_tpRod")

    mdfe30_tpCar = fields.Selection(related="document_id.mdfe30_tpCar")

    mdfe30_UF = fields.Selection(related="document_id.mdfe30_UF")

    mdfe30_veicReboque = fields.One2many(related="document_id.mdfe30_veicReboque")

    mdfe30_lacRodo = fields.One2many(related="document_id.mdfe30_lacRodo")

    @api.depends("document_id.mdfe30_infContratante")
    def _compute_contractor(self):
        for record in self:
            record.mdfe30_infContratante = [
                (6, 0, record.document_id.mdfe30_infContratante.ids)
            ]

    def _prepare_damdfe_values(self):
        if not self:
            return {}

        vehicles = [
            {
                "RNTRC": self.mdfe30_RNTRC,
                "plate": self.mdfe30_placa,
            }
        ]

        for reboque in self.mdfe30_veicReboque:
            vehicles.append(
                {
                    "RNTRC": reboque.mdfe30_prop.mdfe30_RNTRC,
                    "plate": reboque.mdfe30_placa,
                }
            )

        return {
            "vehicles": vehicles,
            "conductors": [
                {
                    "name": cond.mdfe30_xNome,
                    "cpf": cond.mdfe30_CPF,
                }
                for cond in self.mdfe30_condutor
            ],
            "toll": [
                {
                    "resp_cnpj": disp.mdfe30_CNPJPg,
                    "forn_cnpj": disp.mdfe30_CNPJForn,
                    "purchase_number": disp.mdfe30_nCompra,
                }
                for disp in self.mdfe30_disp
            ],
            "ciot": [
                {
                    "code": disp.mdfe30_CIOT,
                }
                for disp in self.mdfe30_infCIOT
            ],
        }


class MDFeModalRodoviarioCIOT(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.ciot"
    _inherit = "mdfe.30.infciot"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_rodoviario_v3_00"
    _mdfe_search_keys = ["mdfe30_CIOT"]
    _description = "Informações do CIOT no Modal Rodoviário MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_CIOT = fields.Char(required=True, size=12)

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


class MDFeModalRodoviarioValePedagioDispositivo(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.vale_pedagio.dispositivo"
    _inherit = "mdfe.30.disp"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_rodoviario_v3_00"
    _description = "Informações de Dispositivos do Pedágio no Modal Rodoviário MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_CNPJForn = fields.Char(required=True)

    mdfe30_vValePed = fields.Monetary(required=True)


class MDFeModalRodoviarioPagamento(spec_models.StackedModel):
    _name = "l10n_br_mdfe.modal.rodoviario.pagamento"
    _inherit = "mdfe.30.rodo_infpag"
    _stacked = "mdfe.30.rodo_infpag"
    _field_prefix = "mdfe30_"
    _schema_name = "mdfe"
    _schema_version = "3.0.0"
    _odoo_module = "l10n_br_mdfe"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_rodoviario_v3_00"
    _spec_module = (
        "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_modal_rodoviario_v3_00"
    )
    _spec_tab_name = "MDFe"
    _description = "Informações do Pagamento do Modal Rodoviário MDFe"

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


class MDFeModalRodoviarioPagamentoFrete(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.pagamento.frete"
    _inherit = "mdfe.30.rodo_comp"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_rodoviario_v3_00"
    _description = "Informações do Frete no Pagamento do Modal Rodoviário MDFe"

    mdfe30_tpComp = fields.Selection(required=True)

    mdfe30_vComp = fields.Monetary(required=True)


class MDFeModalRodoviarioPagamentoPrazo(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.pagamento.prazo"
    _inherit = "mdfe.30.rodo_infprazo"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_rodoviario_v3_00"
    _description = "Informações de Prazo de Pagamento do Modal Rodoviário MDFe"

    mdfe30_nParcela = fields.Char(required=True)

    mdfe30_dVenc = fields.Date(required=True)

    mdfe30_vParcela = fields.Monetary(required=True)


class MDFeModalRodoviarioVeiculoCondutor(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.veiculo.condutor"
    _inherit = "mdfe.30.rodo_condutor"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_rodoviario_v3_00"
    _description = "Informações do Condutor no Modal Rodoviário MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_xNome = fields.Char(required=True)

    mdfe30_CPF = fields.Char(required=True)


class MDFeModalRodoviarioReboque(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.rodoviario.reboque"
    _inherit = "mdfe.30.veicreboque"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_rodoviario_v3_00"
    _description = "Informações de Reboque no Modal Rodoviário MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_prop = fields.Many2one(comodel_name="res.partner")

    mdfe30_placa = fields.Char(required=True)

    mdfe30_tara = fields.Char(required=True)

    mdfe30_capKG = fields.Char(required=True)

    mdfe30_tpCar = fields.Selection(required=True)

    mdfe30_cInt = fields.Char(size=10)

    mdfe30_RENAVAM = fields.Char(size=11)
