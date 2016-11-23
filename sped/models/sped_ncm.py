# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class NCM(models.Model):
    _description = 'NCM'
    _name = 'sped.ncm'
    _order = 'codigo, ex'
    _rec_name = 'ncm'

    codigo = fields.Char('Código', size=8, required=True, index=True)
    ex = fields.Char('EX', size=2, index=True)
    descricao = fields.NameChar('Descrição', size=255, required=True, index=True)
    al_ipi_id = fields.Many2one('sped.aliquota.ipi', string='Alíquota do IPI')
    #cest_ids = fields.Many2many('sped.cest', 'sped_ncm_cest', 'ncm_id', 'cest_id', 'Códigos CEST')

    @api.one
    @api.depends('codigo', 'ex', 'descricao', 'al_ipi_id')
    def _ncm(self):
        self.codigo_formatado = self.codigo[:2] + '.' + self.codigo[2:4] + '.' + self.codigo[4:6] + '.' + self.codigo[6:]
        self.ncm = self.codigo_formatado

        if self.ex:
            self.ncm += '-ex' + self.ex

        self.ncm += ' - ' + self.descricao[:60]

    codigo_formatado = fields.Char(string='NCM', compute=_ncm, store=True)
    ncm = fields.Char(string='NCM', compute=_ncm, store=True)

    def _valida_codigo(self):
        valores = {}
        res = {'value': valores}

        if (not self.codigo) and (not self.ex):
            return res

        if self.id:
            ncm_ids = self.search([('codigo', '=', self.codigo), ('ex', '=', self.ex), ('id', '!=', self.id)])
        else:
            ncm_ids = self.search([('codigo', '=', self.codigo), ('ex', '=', self.ex)])

        if len(ncm_ids) > 0:
            raise ValidationError('Código já existe na tabela!')

        return res

    @api.one
    @api.constrains('codigo', 'ex')
    def constrains_codigo(self):
        self._valida_codigo()

    @api.onchange('codigo', 'ex')
    def onchange_codigo(self):
        return self._valida_codigo()

    ###def name_get(self, cr, uid, ids, context={}):
        ###if not len(ids):
            ###return []

        ###res = []
        ###for cnae in self.browse(cr, uid, ids):
            ###self.descricao = cnae.codigo[:4] + '-' + cnae.codigo[4] + '/' + cnae.codigo[5:]
            ###self.descricao += ' - ' + cnae.descricao
            ###res.append((cnae.id, nome))

        ###return res

    ###def name_search(self, cr, uid, name, args=[], operator='ilike', context={}, limit=100):
        ###if name and operator in ('=', 'ilike', '=ilike', 'like'):
            ###if operator != '=':
                ###name = name.strip().replace(' ', '%')

            ###ids = self.search(cr, uid, [
                ###'|',
                ###('codigo', '=', name),
                ###('descricao', 'ilike', name),
                ###] + args, limit=limit, context=context)

            ###if ids:
                ###return self.name_get(cr, uid, ids, context)

        ###return super(CNAE, self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)


    ###def monta_nome(self, cr, uid, id):
        ###self = self.browse(cr, uid, id)

        ###self.descricao = self.codigo[:2] + '.' + self.codigo[2:4] + '.' + self.codigo[4:6] + '.' + self.codigo[6:]

        ###if self.ex:
            ###self.descricao += '-ex' + self.ex

        ###self.descricao += ' - ' + self.descricao[:40]

        ###return nome

    ###def nome_get(self, cr, uid, ids, context=None):
        ###if not len(ids):
            ###return []

        ###res = []
        ###for id in ids:
            ###res.append((id, self.monta_nome(cr, uid, id)))

        ###return res

    ###def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        ###res = self.nome_get(cr, uid, ids, context=context)
        ###return dict(res)

    ###def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        ###texto = args[0][2]

        ###procura = [
            ###('codigo', 'ilike', texto),
        ###]

        ###return procura

    ###_columns = {
        ###'codigo': fields.char('Código', size=8, required=True, select=True),
        ###'ex': fields.char('EX', size=2, select=True),
        ###'descricao': fields.char('Descrição', size=1500, required=True),
        ###'al_ipi_id': fields.many2one('sped.aliquotaipi', 'Alíquota do IPI', select=True),
        ###'al_pis_cofins_id': fields.many2one('sped.aliquotapiscofins', 'Alíquota do PIS-COFINS', select=True),
        ###'al_ibpt_nacional': fields.float('Alíquota do IBPT', select=True),
        ###'al_ibpt_internacional': fields.float('Alíquota do IBPT internacional', select=True),
        ###'nome': fields.function(_get_nome_funcao, type='char', string='Nome', fnct_search=_procura_nome),
        ####'familiatributaria_id': fields.many2one('sped.familiatributaria', 'Família Tributária', ondelete='restrict', select=True),
        ###'mva_ids': fields.one2many('sped.ncm_mva', 'ncm_id', 'MVAs'),
        ###'familiatributaria_ids': fields.many2many('sped.familiatributaria', 'sped_ncm_familiatributaria', 'ncm_id', 'familiatributaria_id', 'Famílias tributárias'),
        ###'cest_ids': fields.many2many('sped.cest', 'sped_ncm_cest', 'ncm_id', 'cest_id', 'Códigos CEST'),
    ###}

    ###_defaults = {
        ###'codigo': '',
        ###'ex': '',
        ###'descricao': '',
        ###'al_ibpt_nacional': 0,
        ###'al_ibpt_internacional': 0,
    ###}

    ###_rec_name = 'nome'
    ###_order = 'codigo, ex'

    ###_sql_constraints = [
        ###('codigo_ex_unique', 'unique(codigo, ex)', 'O código e a extensão não podem se repetir!'),
    ###]

    ###def busca_aliquota_ipi(self, cr, uid, cst_ipi_entrada, cst_ipi_saida, al_ipi):
        ###ipi_pool = self.pool.get('sped.aliquotaipi')

        ###ipi_ids = ipi_pool.search(cr, uid, [('cst_ipi_entrada', '=', cst_ipi_entrada), ('cst_ipi_saida', '=', cst_ipi_saida), ('al_ipi', '=', al_ipi)])

        ####
        #### Não tem, vou criar
        ####
        ###if not len(ipi_ids):
            ###dados = {
                ###'cst_ipi_entrada': cst_ipi_entrada,
                ###'cst_ipi_saida': cst_ipi_saida,
                ###'al_ipi': al_ipi,
            ###}
            ###ipi_id = ipi_pool.create(cr, uid, dados)
        ###else:
            ###ipi_id = ipi_ids[0]

        ###return ipi_id

    ###def busca_aliquota_pis_cofins(self, cr, uid, cst_pis_cofins_entrada, cst_pis_cofins_saida, al_pis, al_cofins, codigo_justificativa):
        ###pis_cofins_pool = self.pool.get('sped.aliquotapiscofins')

        ###pis_cofins_ids = pis_cofins_pool.search(cr, uid, [('cst_pis_cofins_entrada', '=', cst_pis_cofins_entrada), ('cst_pis_cofins_saida', '=', cst_pis_cofins_saida), ('al_pis', '=', al_pis), ('al_cofins', '=', al_cofins), ('codigo_justificativa', '=', codigo_justificativa)])

        ####
        #### Não tem, vou criar
        ####
        ###if not len(pis_cofins_ids):
            ###dados = {
                ###'cst_pis_cofins_entrada': cst_pis_cofins_entrada,
                ###'cst_pis_cofins_saida': cst_pis_cofins_saida,
                ###'al_pis': al_pis,
                ###'al_cofins': al_cofins,
                ###'codigo_justificativa': codigo_justificativa,
            ###}
            ###pis_cofins_id = pis_cofins_pool.create(cr, uid, dados)
        ###else:
            ###pis_cofins_id = pis_cofins_ids[0]

        ###return pis_cofins_id

    ###def atualiza_ibpt(self, cr, uid, ids, context):
        ###from pybrasil.ncm import NCM_CODIGO_EX
        ###cr.execute('update sped_ncm set al_pis_cofins_id = null, al_ipi_id = null;')

        ###for codigo in NCM_CODIGO_EX:
            ###for ex in NCM_CODIGO_EX[codigo]:
                ###ncm = NCM_CODIGO_EX[codigo][ex]
                ###print(codigo, ex, ncm)

                ###ncm_id = self.search(cr, uid, [('codigo', '=', codigo), ('ex', '=', ex)])

                ###if not len(ncm_id) and len(ex) == 0:
                    ###ncm_id = self.search(cr, uid, [('codigo', '=', codigo), ('ex', '=', False)])

                ###dados = {
                    ###'al_ibpt_nacional': ncm.al_ibpt_nacional,
                    ###'al_ibpt_internacional': ncm.al_ibpt_internacional,
                    ###'ex': ncm.ex
                ###}

                ###if ncm.cst_ipi_entrada:
                    ###ipi_id = self.busca_aliquota_ipi(cr, uid, ncm.cst_ipi_entrada, ncm.cst_ipi_saida, ncm.al_ipi)

                    ###dados['al_ipi_id'] = ipi_id
                ###else:
                    ###dados['al_ipi_id'] = 1

                ###if ncm.cst_pis_cofins_entrada and ncm.cst_pis_cofins_entrada != '50':
                    ###pis_cofins_id = self.busca_aliquota_pis_cofins(cr, uid, ncm.cst_pis_cofins_entrada, ncm.cst_pis_cofins_saida, ncm.al_pis, ncm.al_cofins, ncm.codigo_justificativa_enquadramento_pis_cofins)

                    ###dados['al_pis_cofins_id'] = pis_cofins_id
                ###else:
                    ###dados['al_pis_cofins_id'] = False

                ###if len(ncm_id):
                    ###self.write(cr, uid, ncm_id, dados)

                ###else:
                    ####
                    #### Vamos criar
                    ####
                    ###dados['codigo'] = codigo
                    ###dados['ex'] = ncm.ex
                    ###dados['descricao'] = ncm.descricao[:1500]
                    ###self.create(cr, uid, dados)

###sped_ncm()


###class sped_ncm_mva(osv.Model):
    ###_description = 'NCM - MVA'
    ###_name = 'sped.ncm_mva'
    ###_order = 'ncm_id, estado_id, data_inicio desc'
    ###_columns = {
        ###'ncm_id': fields.many2one('sped.ncm', 'NCM', required=True, ondelete='cascade'),
        ###'estado_id': fields.many2one('sped.estado', 'Estado', required=True, select=True),
        ###'data_inicio': fields.date('Data de início da validade', required=True, select=True),
        ###'mva_normal': CampoPorcentagem('MVA normal'),
        ###'mva_simples': CampoPorcentagem('MVA SIMPLES'),
    ###}

    ###_defaults = {
        ###'data_inicio': lambda *a: time.strftime('%Y-%m-%d'),
        ###'mva_normal': 0,
        ###'mva_simples': 0,
    ###}

    ###_rec_name = 'ncm_id'
    ####_order = 'descricao'

    ###_sql_constraints = [
        ###('ncm_mva_ncm_estado', 'unique (ncm_id, estado_id, data_inicio)', 'O item não pode se repetir!'),
    ###]

###sped_ncm_mva()


###class sped_ncm_familiatributaria(osv.Model):
    ###_description = 'NCM - Família tributária'
    ###_name = 'sped.ncm_familiatributaria'
    ###_order = 'ncm_id, familiatributaria_id'

    ###_columns = {
        ###'ncm_id': fields.many2one('sped.ncm', 'NCM', required=True, ondelete='cascade'),
        ###'familiatributaria_id': fields.many2one('sped.familiatributaria', 'Família Tributária', ondelete='restrict', select=True),
    ###}

    ###_rec_name = 'ncm_id'
    ####_order = 'descricao'

    ####_sql_constraints = [
        ####('ncm_familiatributaria_ncm_familiatributaria', 'unique (ncm_id, familiatributaria_id)', 'O item não pode se repetir!'),
    ####]

###sped_ncm_familiatributaria()
