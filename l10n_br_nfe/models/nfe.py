# Copyright 2019 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons.spec_driven_model.models import spec_models


class NFe(spec_models.StackedModel):
    _name = 'l10n_br_fiscal.document'
    _inherit = ["l10n_br_fiscal.document", "nfe.40.infnfe"]
    _stacked = 'nfe.40.infnfe'
    _stack_skip = ('nfe40_veicTransp')
    _spec_module = 'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe'
#    _concrete_skip = ('nfe.40.det',) # will be mixed in later
    _nfe_search_keys = ['nfe40_Id']

    # all m2o at this level will be stacked even if not required:
    _force_stack_paths = ('infnfe.total',)

    nfe40_versao = fields.Char(related='number')
    nfe40_Id = fields.Char(related='key')

    nfe40_emit = fields.Many2one(
        related="company_id",
        comodel_name="res.company",
        original_spec_model="nfe.40.emit",
    )

    nfe40_dest = fields.Many2one(
        related='partner_id',
        comodel_name='res.partner'

    ) # TODO in invoice

    # TODO should be done by framework?
    nfe40_det = fields.One2many(related='line_ids',
                                comodel_name='l10n_br_fiscal.document.line',
                                inverse_name='document_id')

class NFeLine(spec_models.StackedModel):
    _name = 'l10n_br_fiscal.document.line'
    _inherit = ["l10n_br_fiscal.document.line", "nfe.40.det"]
    _stacked = 'nfe.40.det'
    _spec_module = 'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe'
    _stack_skip = 'nfe40_det_infNFe_id'
    # all m2o below this level will be stacked even if not required:
    _force_stack_paths = ('det.imposto',)
    _rec_name = 'nfe40_xProd'

    nfe40_cProd = fields.Char(related='product_id.code')
    nfe40_xProd = fields.Char(related='product_id.name')
    nfe40_uCom = fields.Char(related='uom_id.name')
    nfe40_vUnCom = fields.Float(related='price')  # TODO sure?
    nfe40_vUnTrib = fields.Float(related='fiscal_price')  # TODO sure?

    nfe40_choice9 = fields.Selection([
        ('normal', 'Produto Normal'),  # overriden to allow normal product
        ('nfe40_veicProd', 'Veículo'),
        ('nfe40_med', 'Medicamento'),
        ('nfe40_arma', 'Arma'),
        ('nfe40_comb', 'Combustível'),
        ('nfe40_nRECOPI', 'Número do RECOPI')],
        "Típo de Produto",
        default="normal")

    def _export_field(self, xsd_fields, class_obj, export_dict):
        if class_obj._name == 'nfe.40.icms':
            xsd_fields = [self.nfe40_choice11]
        return super(NFeLine, self)._export_field(
            xsd_fields, class_obj, export_dict)


class ResCity(models.Model):
    _inherit = "res.city"
    _nfe_search_keys = ['ibge_code']

    # TODO understand why this is still required
    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict,
                            create_m2o=False, model=None):
        "if city not found, break hard, don't create it"
        if parent_dict.get('nfe40_cMun') or parent_dict.get('nfe40_cMunFG'):
            ibge_code = parent_dict.get('nfe40_cMun',
                                        parent_dict.get('nfe40_cMunFG'))
            ibge_code = ibge_code[2:8]
            domain = [('ibge_code', '=', ibge_code)]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False


class Uom(models.Model):
    _inherit = "uom.uom"

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict,
                            create_m2o=False, model=None):
        "if uom not found, break hard, don't create it"
        if rec_dict.get('name'):
            # TODO FIXME where are the BR unit names supposed to live?
            BR2ODOO = {'UN': 'Unit(s)', 'LU': 'Liter(s)'}
            name = BR2ODOO.get(rec_dict['name'], rec_dict['name'])
            domain = [('name', '=', name)]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False


class ResCountryState(models.Model):
    _inherit = "res.country.state"
    _nfe_search_keys = ['ibge_code', 'code']
    _nfe_extra_domain = [('ibge_code', '!=', False)]
