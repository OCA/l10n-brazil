# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields
from odoo.addons.spec_driven_model.models import spec_models

ICMS_ST_CST_CODES = ['60',]


class NFeLine(spec_models.StackedModel):
    _name = 'l10n_br_fiscal.document.line'
    _inherit = ["l10n_br_fiscal.document.line", "nfe.40.det"]
    _stacked = 'nfe.40.det'
    _spec_module = 'odoo.addons.l10n_br_spec_nfe.models.v4_00.leiauteNFe'
    _stack_skip = 'nfe40_det_infNFe_id'
    # all m2o below this level will be stacked even if not required:
    _force_stack_paths = ('det.imposto',)
    _rec_name = 'nfe40_xProd'

    # The generateDS prod mixin (prod XML tag) cannot be inject in
    # the product.product object because the tag embeded values from the
    # fiscal document line. So the mapping is done:
    # from Odoo -> XML by using related fields/_compute
    # from XML -> Odoo by overriding the product create method
    nfe40_cProd = fields.Char(
        related='product_id.default_code',
    )

    nfe40_xProd = fields.Char(
        related='product_id.name',
    )

    nfe40_cEAN = fields.Char(
        related='product_id.barcode',
    )

    nfe40_cEANTrib = fields.Char(
        related='product_id.barcode',
    )

    nfe40_uCom = fields.Char(
        related='product_id.uom_id.code',
        inverse='_inverse_uCom',
    )

    nfe40_uTrib = fields.Char(
        related='product_id.uom_id.code',
    )

    nfe40_vUnCom = fields.Float(
        related='price_unit',
    )

    nfe40_vUnTrib = fields.Float(
        related='fiscal_price',
    )

    nfe40_choice9 = fields.Selection([
        ('normal', 'Produto Normal'),  # overriden to allow normal product
        ('nfe40_veicProd', 'Veículo'),
        ('nfe40_med', 'Medicamento'),
        ('nfe40_arma', 'Arma'),
        ('nfe40_comb', 'Combustível'),
        ('nfe40_nRECOPI', 'Número do RECOPI')],
        "Típo de Produto",
        default="normal")

    nfe40_choice11 = fields.Selection(
        compute='_compute_choice11',
        store=True,
    )

    nfe40_choice12 = fields.Selection(
        compute='_compute_choice12',
        store=True,
    )

    nfe40_choice15 = fields.Selection(
        compute='_compute_choice15',
        store=True,
    )

    nfe40_choice3 = fields.Selection(
        compute='_compute_choice3',
        store=True,
    )

    nfe40_choice20 = fields.Selection(
        compute='_compute_nfe40_choice20',
        store=True,
    )

    nfe40_choice13 = fields.Selection(
        compute='_compute_nfe40_choice13',
        store=True,
    )

    nfe40_choice16 = fields.Selection(
        compute='_compute_nfe40_choice16',
        store=True,
    )

    nfe40_orig = fields.Selection(
        related='icms_origin',
    )

    nfe40_modBC = fields.Selection(
        related='icms_base_type',
    )

    nfe40_vBC = fields.Monetary(
        related='icms_base',
    )

    nfe40_vICMS = fields.Monetary(
        related='icms_value',
    )

    nfe40_vPIS = fields.Monetary(
        related='pis_value',
    )

    nfe40_vCOFINS = fields.Monetary(
        related='cofins_value',
    )

    nfe40_CFOP = fields.Char(
        related='cfop_id.code',
    )

    nfe40_indTot = fields.Selection(
        default='1',
    )

    nfe40_vIPI = fields.Monetary(
        related='ipi_value',
    )

    nfe40_infAdProd = fields.Char(
        related='additional_data',
    )

    @api.depends('icms_cst_id')
    def _compute_choice11(self):
        for record in self:
            if record.icms_cst_id.code == '00':
                record.nfe40_choice11 = 'nfe40_ICMS00'
            elif record.icms_cst_id.code == '10':
                record.nfe40_choice11 = 'nfe40_ICMS10'
            elif record.icms_cst_id.code == '20':
                record.nfe40_choice11 = 'nfe40_ICMS20'
            elif record.icms_cst_id.code == '30':
                record.nfe40_choice11 = 'nfe40_ICMS30'
            elif record.icms_cst_id.code in ['40', '41', '50']:
                record.nfe40_choice11 = 'nfe40_ICMS40'
            elif record.icms_cst_id.code == '51':
                record.nfe40_choice11 = 'nfe40_ICMS51'
            elif record.icms_cst_id.code == '60':
                record.nfe40_choice11 = 'nfe40_ICMS60'
            elif record.icms_cst_id.code == '70':
                record.nfe40_choice11 = 'nfe40_ICMS70'
            elif record.icms_cst_id.code == '90':
                record.nfe40_choice11 = 'nfe40_ICMS90'
            elif record.icms_cst_id.code == '400':
                record.nfe40_choice11 = 'nfe40_ICMSSN102'

    @api.depends('pis_cst_id')
    def _compute_choice12(self):
        for record in self:
            if record.pis_cst_id.code in ['01', '02']:
                record.nfe40_choice12 = 'nfe40_PISAliq'
            elif record.pis_cst_id.code == '03':
                record.nfe40_choice12 = 'nfe40_PISQtde'
            elif record.pis_cst_id.code in ['04', '06', '07', '08', '09']:
                record.nfe40_choice12 = 'nfe40_PISNT'
            else:
                record.nfe40_choice12 = 'nfe40_PISOutr'

    @api.depends('cofins_cst_id')
    def _compute_choice15(self):
        for record in self:
            if record.cofins_cst_id.code in ['01', '02']:
                record.nfe40_choice15 = 'nfe40_COFINSAliq'
            elif record.cofins_cst_id.code == '03':
                record.nfe40_choice15 = 'nfe40_COFINSQtde'
            elif record.cofins_cst_id.code in ['04', '06', '07', '08', '09']:
                record.nfe40_choice15 = 'nfe40_COFINSNT'
            else:
                record.nfe40_choice15 = 'nfe40_COFINSOutr'

    @api.depends('ipi_cst_id')
    def _compute_choice3(self):
        for record in self:
            if record.ipi_cst_id.code in ['00', '49', '50', '99']:
                record.nfe40_choice3 = 'nfe40_IPITrib'
            else:
                record.nfe40_choice3 = 'nfe40_IPINT'

    @api.depends('ipi_base_type')
    def _compute_nfe40_choice20(self):
        for record in self:
            if record.ipi_base_type == 'percent':
                record.nfe40_choice20 = 'nfe40_pIPI'
            else:
                record.nfe40_choice20 = 'nfe40_vUnid'

    @api.depends('ipi_base_type')
    def _compute_nfe40_choice13(self):
        for record in self:
            if record.pis_base_type == 'percent':
                record.nfe40_choice13 = 'nfe40_pPIS'
            else:
                record.nfe40_choice13 = 'nfe40_vAliqProd'

    @api.depends('ipi_base_type')
    def _compute_nfe40_choice16(self):
        for record in self:
            if record.pis_base_type == 'percent':
                record.nfe40_choice16 = 'nfe40_pCOFINS'
            else:
                record.nfe40_choice16 = 'nfe40_vAliqProd'

    def _inverse_uCom(self):
        # TODO need fix in search in l10n_br_fiscal/models/uom_uom.py
        for line in self:
            if line.nfe40_uCom:
                uom_ids = self.env['uom.uom'].search(
                    [('code', 'ilike', line.nfe40_uCom)])
                if uom_ids:
                    line.uom_id = uom_ids[0]

    def _export_fields(self, xsd_fields, class_obj, export_dict):
        if class_obj._name == 'nfe.40.icms':
            xsd_fields = [self.nfe40_choice11]
        elif class_obj._name == 'nfe.40.tipi':
            xsd_fields = [f for f in xsd_fields if f not in [
                i[0] for i in class_obj._fields['nfe40_choice3'].selection]]
            xsd_fields += [self.nfe40_choice3]
        elif class_obj._name == 'nfe.40.pis':
            xsd_fields = [self.nfe40_choice12]
        elif class_obj._name == 'nfe.40.cofins':
            xsd_fields = [self.nfe40_choice15]
        elif class_obj._name == 'nfe.40.ipitrib':
            xsd_fields = [i for i in xsd_fields]
            if self.nfe40_choice20 == 'nfe40_pIPI':
                xsd_fields.remove('nfe40_qUnid')
                xsd_fields.remove('nfe40_vUnid')
            else:
                xsd_fields.remove('nfe40_vBC')
                xsd_fields.remove('nfe40_pIPI')
        elif class_obj._name == 'nfe.40.pisoutr':
            xsd_fields = [i for i in xsd_fields]
            if self.nfe40_choice13 == 'nfe40_pPIS':
                xsd_fields.remove('nfe40_qBCProd')
                xsd_fields.remove('nfe40_vAliqProd')
            else:
                xsd_fields.remove('nfe40_vBC')
                xsd_fields.remove('nfe40_pPIS')
        elif class_obj._name == 'nfe.40.cofinsoutr':
            xsd_fields = [i for i in xsd_fields]
            if self.nfe40_choice16 == 'nfe40_pCOFINS':
                xsd_fields.remove('nfe40_qBCProd')
                xsd_fields.remove('nfe40_vAliqProd')
            else:
                xsd_fields.remove('nfe40_vBC')
                xsd_fields.remove('nfe40_pCOFINS')

        if self.ncm_id and self.ncm_id.code:
            self.nfe40_NCM = self.ncm_id.code.replace('.', '') # TODO via _compute
        else:
            self.nfe40_NCM = ''
        self.nfe40_CEST = self.cest_id and \
            self.cest_id.code.replace('.', '') or False
        self.nfe40_qCom = self.quantity
        self.nfe40_qTrib = self.quantity
        self.nfe40_pICMS = self.icms_percent
        self.nfe40_pIPI = self.ipi_percent
        self.nfe40_pPIS = self.pis_percent
        self.nfe40_pCOFINS = self.cofins_percent
        self.nfe40_cEnq = str(self.ipi_guideline_id.code or '999'
                              ).zfill(3)

        if self.document_id.ind_final == '1' and \
                self.document_id.nfe40_idDest == '2' and \
                self.document_id.nfe40_indIEDest == '9':
            self.nfe40_vBCUFDest = self.nfe40_vBC
            if self.document_id.partner_id.state_id.code in [
                    'AC', 'CE', 'ES', 'GO', 'MT', 'MS', 'PA', 'PI', 'RR', 'SC'
            ]:
                self.nfe40_pICMSUFDest = 17.0
            elif self.document_id.partner_id.state_id.code == 'RO':
                self.nfe40_pICMSUFDest = 17.5
            elif self.document_id.partner_id.state_id.code in [
                    'AM', 'AP', 'BA', 'DF', 'MA', 'MG', 'PB', 'PR', 'PE',
                    'RN', 'RS', 'SP', 'SE', 'TO'
            ]:
                self.nfe40_pICMSUFDest = 18.0
            elif self.document_id.partner_id.state_id.code == 'RJ':
                self.nfe40_pICMSUFDest = 20.0
            self.nfe40_pICMSInter = '7.00'
            self.nfe40_pICMSInterPart = 100.0
            self.nfe40_vICMSUFDest = (
                self.nfe40_vBCUFDest * (
                    (self.nfe40_pICMSUFDest - float(
                        self.nfe40_pICMSInter)
                     ) / 100) * (self.nfe40_pICMSInterPart / 100))
            self.nfe40_vICMSUFRemet = (
                self.nfe40_vBCUFDest * (
                    (self.nfe40_pICMSUFDest - float(
                        self.nfe40_pICMSInter)
                     ) / 100) * ((100 - self.nfe40_pICMSInterPart
                                  ) / 100))

        return super()._export_fields(xsd_fields, class_obj, export_dict)

    def _export_field(self, xsd_field, class_obj, member_spec):
        # ISSQN
        if xsd_field == 'nfe40_cMunFG':
            return self.issqn_fg_city_id.state_id.ibge_code + self.issqn_fg_city_id.ibge_code
        if xsd_field == 'nfe40_cListServ':
            return self.service_type_id.code
        if xsd_field == 'nfe40_vDeducao':
            return self.issqn_deduction_amount
        if xsd_field == 'nfe40_vOutro':
            return self.issqn_other_amount
        if xsd_field == 'nfe40_vDescIncond':
            return self.issqn_desc_incond_amount
        if xsd_field == 'nfe40_vDescCond':
            return self.issqn_desc_cond_amount
        if xsd_field == 'nfe40_vISSRet':
            return self.issqn_wh_value
        if xsd_field == 'nfe40_indISS':
            return self.issqn_eligibility
        if xsd_field == 'nfe40_cServico':
            return '' # TODO
        if xsd_field == 'nfe40_cMun':
            return self.issqn_fg_city_id.state_id.ibge_code + self.issqn_fg_city_id.ibge_code  # TODO
        if xsd_field == 'nfe40_cPais':
            return self.issqn_fg_city_id.state_id.country_id.bc_code[1:] # TODO
        if xsd_field == 'nfe40_nProcesso':
            return '' # TODO
        if xsd_field == 'nfe40_indIncentivo':
            return self.issqn_incentive
        if xsd_field == 'nfe40_xProd':
            return self.name

        if xsd_field in ['nfe40_cEAN', 'nfe40_cEANTrib'] and \
                not self[xsd_field]:
            return 'SEM GTIN'
        elif xsd_field == 'nfe40_CST':
            if class_obj._name.startswith('nfe.40.icms'):
                return self.icms_cst_id.code
            elif class_obj._name.startswith('nfe.40.ipi'):
                return self.ipi_cst_id.code
            elif class_obj._name.startswith('nfe.40.pis'):
                return self.pis_cst_id.code
            elif class_obj._name.startswith('nfe.40.cofins'):
                return self.cofins_cst_id.code
        elif xsd_field == 'nfe40_vBC':
            field_name = 'nfe40_vBC'
            if class_obj._name.startswith('nfe.40.icms'):
                field_name = 'icms_base'
            elif class_obj._name.startswith('nfe.40.ipi'):
                field_name = 'ipi_base'
            elif class_obj._name.startswith('nfe.40.pis'):
                field_name = 'pis_base'
            elif class_obj._name.startswith('nfe.40.cofins'):
                field_name = 'cofins_base'
            return self._export_float_monetary(
                field_name, member_spec, class_obj,
                class_obj._fields[xsd_field]._attrs.get('xsd_required'))
        elif xsd_field in ('nfe40_vBCSTRet', 'nfe40_pST',
                           'nfe40_vICMSSubstituto', 'nfe40_vICMSSTRet'):
            if self.icms_cst_id.code in ICMS_ST_CST_CODES:
                return self._export_float_monetary(
                    xsd_field, member_spec, class_obj, True)
        else:
            return super()._export_field(xsd_field, class_obj, member_spec)

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if not self[field_name] and not xsd_required:
            if not any(self[f] for f in self[field_name]._fields
                       if self._fields[f]._attrs.get('xsd')) and \
                    field_name not in ['nfe40_PIS', 'nfe40_COFINS']:
                return False
        if field_name == 'nfe40_ISSQN' and \
                not self.service_type_id: # TODO
            self[field_name] = False
            return False
        if field_name == 'nfe40_ICMS' and \
                self.service_type_id: # TODO
            self[field_name] = False
            return False
        if field_name in ['nfe40_II', 'nfe40_PISST', 'nfe40_COFINSST']:
            self[field_name] = False
            return False
        return super()._export_many2one(field_name, xsd_required, class_obj)

    def _export_float_monetary(self, field_name, member_spec, class_obj,
                               xsd_required):
        if field_name == 'nfe40_vProd' and class_obj._name == 'nfe.40.prod':
            self[field_name] = self['nfe40_qCom'] * self['nfe40_vUnCom']
        if field_name == 'nfe40_pICMSInterPart':
            self[field_name] = 100.0
        if not self[field_name] and not xsd_required:
            if not (class_obj._name == 'nfe.40.imposto' and
                    field_name == 'nfe40_vTotTrib') and not \
                    (class_obj._name == 'nfe.40.fat'):
                self[field_name] = False
                return False
        return super()._export_float_monetary(
            field_name, member_spec, class_obj, xsd_required)

    def _build_attr(self, node, fields, vals, path, attr, create_m2o,
                    defaults):
        key = "nfe40_%s" % (attr.get_name(),)  # TODO schema wise
        value = getattr(node, attr.get_name())

        if key.startswith('nfe40_ICMS') and key not in [
                'nfe40_ICMS', 'nfe40_ICMSTot', 'nfe40_ICMSUFDest']:
            vals['nfe40_choice11'] = key

        if key.startswith('nfe40_IPI') and key != 'nfe40_IPI':
            vals['nfe40_choice3'] = key

        if key.startswith('nfe40_PIS') and key not in [
                'nfe40_PIS', 'nfe40_PISST']:
            vals['nfe40_choice12'] = key

        if key.startswith('nfe40_COFINS') and key not in [
                'nfe40_COFINS', 'nfe40_COFINSST']:
            vals['nfe40_choice15'] = key

        if key == 'nfe40_vUnCom':
            vals['price_unit'] = float(value)
        if key == 'nfe40_NCM':
            ncm = '.'.join([value[i:i+2] for i in range(0, len(value), 2)])
            vals['ncm_id'] = self.env['l10n_br_fiscal.ncm'].search([
                ('code', '=', ncm)], limit=1).id
        if key == 'nfe40_CEST' and value:
            cest = value[:2] + '.' + value[2:5] + '.' + value[5:]
            vals['cest_id'] = self.env['l10n_br_fiscal.cest'].search([
                ('code', '=', cest)], limit=1).id
        if key == 'nfe40_qCom':
            vals['quantity'] = float(value)
            vals['fiscal_quantity'] = float(value)
        if key == 'nfe40_pICMS':
            vals['icms_percent'] = float(value or 0.00)
        if key == 'nfe40_pIPI':
            vals['ipi_percent'] = float(value or 0.00)
        if key == 'nfe40_pPIS':
            vals['pis_percent'] = float(value or 0.00)
        if key == 'nfe40_pCOFINS':
            vals['cofins_percent'] = float(value or 0.00)
        if key == 'nfe40_cEnq':
            code = str(int(value))
            vals['ipi_guideline_id'] = \
                self.env['l10n_br_fiscal.tax.ipi.guideline'].search([
                    ('code', '=', code)], limit=1).id

        return super()._build_attr(
            node, fields, vals, path, attr, create_m2o, defaults)

    def _build_string_not_simple_type(self, key, vals, value, node):
        if key not in ['nfe40_CST', 'nfe40_modBC', 'nfe40_CSOSN']:
            super()._build_string_not_simple_type(
                key, vals, value, node)
            # TODO avoid collision with cls prefix
        elif key == 'nfe40_CST':
            if node.original_tagname_.startswith('ICMS'):
                vals['icms_cst_id'] = \
                    self.env['l10n_br_fiscal.cst'].search(
                        [('code', '=', value),
                         ('tax_domain', '=', 'icms')])[0].id
            if node.original_tagname_.startswith('IPI'):
                vals['ipi_cst_id'] = \
                    self.env['l10n_br_fiscal.cst'].search(
                        [('code', '=', value),
                         ('tax_domain', '=', 'ipi')])[0].id
            if node.original_tagname_.startswith('PIS'):
                vals['pis_cst_id'] = \
                    self.env['l10n_br_fiscal.cst'].search(
                        [('code', '=', value),
                         ('tax_domain', '=', 'pis')])[0].id
            if node.original_tagname_.startswith('COFINS'):
                vals['cofins_cst_id'] = \
                    self.env['l10n_br_fiscal.cst'].search(
                        [('code', '=', value),
                         ('tax_domain', '=', 'cofins')])[0].id
        elif key == 'nfe40_modBC':
            vals['icms_base_type'] = value

    def _build_many2one(self, comodel, vals, new_value, key, create_m2o):
        if self._name == 'account.invoice.line' and \
                comodel._name == 'l10n_br_fiscal.document.line':
            # TODO do not hardcode!!
            # stacked m2o
            vals.update(new_value)
        else:
            super()._build_many2one(comodel, vals, new_value, key, create_m2o)

    def _verify_related_many2ones(self, related_many2ones):
        if related_many2ones.get('product_id', {}).get('barcode') and \
                related_many2ones['product_id']['barcode'] == 'SEM GTIN':
            del related_many2ones['product_id']['barcode']
        return super()._verify_related_many2ones(related_many2ones)

    def _get_aditional_keys(self, model, rec_dict, keys):
        keys = super()._get_aditional_keys(model, rec_dict, keys)
        if model._name == 'product.product' and rec_dict.get('barcode'):
            return ['barcode'] + keys
        return keys
