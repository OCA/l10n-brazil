# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
from pybrasil.valor import formata_valor


class AliquotaSIMPLESAnexo(models.Model):
    _description = 'Anexo do SIMPLES Nacional'
    _name = 'sped.aliquota.simples.anexo'
    _rec_name = 'nome'
    _order = 'nome'

    nome = fields.Char('Anexo do SIMPLES Nacional', size=40, index=True)
    aliquota_ids = fields.One2many('sped.aliquota.simples.aliquota', 'anexo_id', 'Alíquotas')

    def _valida_nome(self):
        valores = {}
        res = {'value': valores}

        if not self.nome:
            return res

        if self.id:
            cnae_ids = self.search([('nome', '=', self.nome), ('id', '!=', self.id)])
        else:
            cnae_ids = self.search([('nome', '=', self.nome)])

        if len(cnae_ids) > 0:
            raise ValidationError('Anexo já existe na tabela!')

        return res

    @api.one
    @api.constrains('nome')
    def constrains_nome(self):
        self._valida_nome()

    @api.onchange('nome')
    def onchange_nome(self):
        return self._valida_nome()


class AliquotaSIMPLESTeto(models.Model):
    _description = 'Teto do SIMPLES Nacional'
    _name = 'sped.aliquota.simples.teto'
    _rec_name = 'nome'
    _order = 'valor'

    valor = fields.Dinheiro('Valor do teto do SIMPLES Nacional', required=True, index=True)
    nome = fields.Char('Teto do SIMPLES Nacional', size=40, index=True)

    def _valida_valor(self):
        valores = {}
        res = {'value': valores}

        if not self.valor:
            return res

        if self.id:
            cnae_ids = self.search([('valor', '=', self.valor), ('id', '!=', self.id)])
        else:
            cnae_ids = self.search([('valor', '=', self.valor)])

        if len(cnae_ids) > 0:
            raise ValidationError('Valor já existe na tabela!')

        return res

    @api.one
    @api.constrains('valor')
    def constrains_valor(self):
        self._valida_valor()

    @api.onchange('valor')
    def onchange_valor(self):
        return self._valida_valor()


class AliquotaSIMPLESAliquota(models.Model):
    _description = 'Alíquota do SIMPLES Nacional'
    _name = 'sped.aliquota.simples.aliquota'
    _rec_name = 'al_simples'
    _order = 'anexo_id, teto_id'

    anexo_id = fields.Many2one('sped.aliquota.simples.anexo', 'Anexo', required=True, ondelete='cascade')
    teto_id = fields.Many2one('sped.aliquota.simples.teto', 'Teto', required=True, ondelete='cascade')
    al_simples = fields.Porcentagem('SIMPLES')
    al_irpj = fields.Porcentagem('IRPJ')
    al_csll = fields.Porcentagem('CSLL')
    al_cofins = fields.Porcentagem('COFINS')
    al_pis = fields.Porcentagem('PIS')
    al_cpp = fields.Porcentagem('CPP')
    al_icms = fields.Porcentagem('ICMS')
    al_iss = fields.Porcentagem('ISS')



##
## Alíquotas padrão para o crédito do ICMS para emissores do SIMPLES Nacional
##
#class AliquotaICMSSN(orm.Model):
    #_description = 'Alíquota de crédito do ICMS SIMPLES'
    #_name = 'sped.aliquotaicmssn'

    #def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        #retorno = {}
        #txt = ''

        #for registro in self.browse(cursor, user_id, ids):
            #if registro.al_icms == -1:
                #txt = 'Não tributado'
            #else:
                #txt = '%.2f%%' % registro.al_icms
                #txt = txt.replace('.', ',')

                #if registro.rd_icms != 0:
                    #txt += ', com redução de %.2f%%' % registro.rd_icms

                #if len(registro.observacao):
                    #txt += ' - ' + registro.observacao

            #retorno[registro.id] = txt

        #return retorno

    #def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        #texto = args[0][2]

        #procura = [
            #('al_icms', '>=', texto),
            #]
        #return procura

    #_columns = {
        #'al_icms': CampoPorcentagem('Alíquota do crédito de ICMS', required=True,
            #help='Alíquotas definidas na <a href="http://www.receita.fazenda.gov.br/Legislacao/LeisComplementares/2006/leicp123ConsolidadaCGSN.htm" target="_blank">Lei Complementar nº 123, de 14 de dezembro de 2006</a>.'),
        #'rd_icms': CampoPorcentagem('Percentual estadual de redução da alíquota de ICMS',
            #help='Caso haja legislação estadual que prescreva redução do percentual de partilha do ICMS para empresas do SIMPLES Nacional, informe aqui o valor percentual dessa redução. Exemplo: no Paraná, há o <a href="http://www.sefanet.pr.gov.br/SEFADocumento/Arquivos/2200904248.pdf">Decreto Estadual nº 4.248/2009</a>.'),
        #'observacao': fields.char('Observação', size=60),
        #'descricao': fields.function(_descricao, string='Descrição', method=True, type='char', fnct_search=_procura_descricao),
        #}

    #_defaults = {
        #'al_icms': 0.00,
        #'rd_icms': 0.00,
        #}

    #_rec_name = 'descricao'
    #_order = 'al_icms'

    #_sql_constraints = [
        #('al_icms_rd_icms_unique', 'unique (al_icms, rd_icms)',
        #'A alíquota de crédito do ICMS SIMPLES não pode se repetir!'),
        #]
