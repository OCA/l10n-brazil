# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
from pybrasil.valor import formata_valor


class ProtocoloICMS(models.Model):
    _description = 'Protocolos ICMS'
    _name = 'sped.protocolo.icms'
    _rec_name = 'descricao'
    _order = 'descricao'

    tipo = fields.Selection([('P', 'Próprio'), ('S', 'ST')], 'Tipo', required=True, default='P', index=True)
    descricao = fields.Char('Protocolo', size=60, index=True, required=True)
    #ncm_ids = fields.Many2many('sped.ncm', 'sped_protocolo_icms_ncm', 'protocolo_id', 'ncm_id', 'NCMs')
    #produto_ids = fields.Many2many('cadastro.produto', 'sped_protocolo_icms_produto', 'protocolo_id', 'produto_id', 'Produtos')
    estado_ids = fields.Many2many('sped.estado', 'sped_protocolo_icms_estado', 'protocolo_id', 'estado_id', string='Estados')

    aliquota_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas')
    aliquota_interna_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas internas', domain=[('interna', '=', True)])
    aliquota_AC_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Acre', domain=[('estado_origem_id.uf', '=', 'AC')])
    aliquota_AL_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas de Alagoas', domain=[('estado_origem_id.uf', '=', 'AL')])
    aliquota_AP_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Amapá', domain=[('estado_origem_id.uf', '=', 'AP')])
    aliquota_AM_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Amazonas', domain=[('estado_origem_id.uf', '=', 'AM')])
    aliquota_BA_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas da Bahia', domain=[('estado_origem_id.uf', '=', 'BA')])
    aliquota_CE_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Ceará', domain=[('estado_origem_id.uf', '=', 'CE')])
    aliquota_DF_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Distrito Federal', domain=[('estado_origem_id.uf', '=', 'DF')])
    aliquota_ES_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Espírito Santo', domain=[('estado_origem_id.uf', '=', 'ES')])
    #aliquota_EX_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Exterior', domain=[('estado_origem_id.uf', '=', 'EX')])
    aliquota_GO_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas de Goiás', domain=[('estado_origem_id.uf', '=', 'GO')])
    aliquota_MA_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Maranhão', domain=[('estado_origem_id.uf', '=', 'MA')])
    aliquota_MT_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Mato Grosso', domain=[('estado_origem_id.uf', '=', 'MT')])
    aliquota_MS_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Mato Grosso do Sul', domain=[('estado_origem_id.uf', '=', 'MS')])
    aliquota_MG_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas de Minas Gerais', domain=[('estado_origem_id.uf', '=', 'MG')])
    aliquota_PA_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Pará', domain=[('estado_origem_id.uf', '=', 'PA')])
    aliquota_PB_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas da Paraíba', domain=[('estado_origem_id.uf', '=', 'PB')])
    aliquota_PR_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Paraná', domain=[('estado_origem_id.uf', '=', 'PR')])
    aliquota_PE_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas de Pernambuco', domain=[('estado_origem_id.uf', '=', 'PE')])
    aliquota_PI_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Piauí', domain=[('estado_origem_id.uf', '=', 'PI')])
    aliquota_RJ_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Rio de Janeiro', domain=[('estado_origem_id.uf', '=', 'RJ')])
    aliquota_RN_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Rio Grande do Norte', domain=[('estado_origem_id.uf', '=', 'RN')])
    aliquota_RS_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Rio Grande do Sul', domain=[('estado_origem_id.uf', '=', 'RS')])
    aliquota_RO_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas de Rondônia', domain=[('estado_origem_id.uf', '=', 'RO')])
    aliquota_RR_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas de Roraima', domain=[('estado_origem_id.uf', '=', 'RR')])
    aliquota_SC_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas de Santa Catarina', domain=[('estado_origem_id.uf', '=', 'SC')])
    aliquota_SP_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas de São Paulo', domain=[('estado_origem_id.uf', '=', 'SP')])
    aliquota_SE_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas de Sergipe', domain=[('estado_origem_id.uf', '=', 'SE')])
    aliquota_TO_ids = fields.One2many('sped.protocolo.icms.aliquota', 'protocolo_id', 'Alíquotas do Tocantins', domain=[('estado_origem_id.uf', '=', 'TO')])

    def _valida_descricao(self):
        valores = {}
        res = {'value': valores}

        if self.descricao:
            sql = u"""
            select
                a.id
            from
                sped_protocolo_icms a
            where
                a.descricao = '{descricao}'
            """
            sql = sql.format(descricao=self.descricao)

            if self.id or self._origin.id:
                sql += u"""
                    and a.id != {id}
                """
                sql = sql.format(id=self.id or self._origin.id)

            self.env.cr.execute(sql)
            jah_existe = self.env.cr.fetchall()

            if jah_existe:
                raise ValidationError('Protocolo já existe!')

        return res

    @api.one
    @api.constrains('descricao')
    def constrains_descricao(self):
        self._valida_descricao()

    @api.onchange('descricao')
    def onchange_descricao(self):
        return self._valida_descricao()

    @api.one
    def atualizar_tabela(self):
        if self.descricao != 'Padrão':
            return

        sped_estado = self.env['sped.estado']
        sped_aliquota_icms = self.env['sped.aliquota.icms.proprio']
        sped_protocolo_icms_aliquota = self.env['sped.protocolo.icms.aliquota']

        self._cr.execute('delete from sped_protocolo_icms_aliquota where protocolo_id = ' + str(self.id) + ';')

        for estado_origem in ALIQUOTAS_ICMS:
            estado_origem_ids = sped_estado.search([('uf', '=', estado_origem)])

            for estado_destino in ALIQUOTAS_ICMS[estado_origem]:
                estado_destino_ids = sped_estado.search([('uf', '=', estado_destino)])
                al_icms_ids = sped_aliquota_icms.search([('al_icms', '=', ALIQUOTAS_ICMS[estado_origem][estado_destino]), ('md_icms', '=', '3'), ('rd_icms', '=', 0)])

                dados = {
                    'protocolo_id': self.id,
                    'data_inicio': '2016-01-01',
                    'estado_origem_id': estado_origem_ids[0].id,
                    'estado_destino_id': estado_destino_ids[0].id,
                    'al_icms_proprio_id': al_icms_ids[0].id,
                }

                sped_protocolo_icms_aliquota.create(dados)

    @api.one
    def atualizar_sped_st(self):
        sped_estado = self.env['sped.estado']
        sped_aliquota_icms = self.env['sped.aliquota.icms.proprio']
        sped_aliquota_st = self.env['sped.aliquota.icms.st']
        sped_protocolo_icms_aliquota = self.env['sped.protocolo.icms.aliquota']

        self._cr.execute('delete from sped_protocolo_icms_aliquota where protocolo_id = ' + str(self.id) + ';')

        for estado_origem in ALIQUOTAS_ICMS:
            estado_origem_ids = sped_estado.search([('uf', '=', estado_origem)])

            for estado_destino in ALIQUOTAS_ICMS[estado_origem]:
                estado_destino_ids = sped_estado.search([('uf', '=', estado_destino)])
                al_icms_ids = sped_aliquota_icms.search([('al_icms', '=', ALIQUOTAS_ICMS[estado_origem][estado_destino]), ('md_icms', '=', '3'), ('rd_icms', '=', 0)])
                al_icms_st_ids = sped_aliquota_st.search([('al_icms', '=', ALIQUOTAS_ICMS[estado_destino][estado_destino]), ('md_icms', '=', '4'), ('rd_icms', '=', 0),  ('rd_mva', '=', 0)])

                dados = {
                    'protocolo_id': self.id,
                    'data_inicio': '2016-01-01',
                    'estado_origem_id': estado_origem_ids[0].id,
                    'estado_destino_id': estado_destino_ids[0].id,
                    'al_icms_proprio_id': al_icms_ids[0].id,
                    'al_icms_st_id': al_icms_st_ids[0].id,
                }

                sped_protocolo_icms_aliquota.create(dados)

    ncm = fields.Char('NCM', size=8)
    ex = fields.Char('EX', size=2)
    mva = fields.Porcentagem('MVA original')
    ncm_ids = fields.One2many('sped.protocolo.icms.ncm', 'protocolo_id', 'NCMs')

    @api.one
    @api.depends('tipo', 'ncm', 'ex', 'mva')
    def exclui_ncm(self):
        #
        # Excluímos os anteriores
        #
        if not self.ncm:
            return

        protocolo_ncm = self.env['sped.protocolo.icms.ncm']

        if self.ex:
            protocolo_ncm_ids = protocolo_ncm.search([('protocolo_id', '=', self.id), ('ncm_id.codigo', '=ilike', self.ncm), ('ncm_id.ex', '=', self.ex)])

        else:
            protocolo_ncm_ids = protocolo_ncm.search([('protocolo_id', '=', self.id), ('ncm_id.codigo', '=ilike', self.ncm)])

        protocolo_ncm_ids.unlink()

    @api.one
    @api.depends('tipo', 'ncm', 'ex', 'mva')
    def insere_ncm(self):
        if (self.tipo == 'P' and (not self.ncm)) or (self.tipo == 'S' and (not (self.ncm and self.mva))):
            return

        #
        # Excluímos os anteriores
        #
        self.exclui_ncm()

        sped_ncm = self.env['sped.ncm']

        if self.ex:
            ncm_ids = sped_ncm.search([('codigo', 'ilike', self.ncm), ('ex', '=', self.ex)])
        else:
            ncm_ids = sped_ncm.search([('codigo', 'ilike', self.ncm)])

        protocolo_ncm = self.env['sped.protocolo.icms.ncm']

        for ncm_obj in ncm_ids:
            dados = {
                'protocolo_id': self.id,
                'ncm_id': ncm_obj.id,
                'mva': self.mva,
            }
            protocolo_ncm.create(dados)

        self.ncm = ''
        self.ex = ''
        self.mva = 0


class ProtocoloICMSAliquota(models.Model):
    _description = 'Protocolo ICMS - alíquotas'
    _name = 'sped.protocolo.icms.aliquota'
    #_rec_name = 'descricao'
    _order = 'protocolo_id, data_inicio desc, estado_origem_id, estado_destino_id'

    protocolo_id = fields.Many2one('sped.protocolo.icms', 'Protocolo', require=True, ondelete='cascade')
    estado_origem_id = fields.Many2one('sped.estado', 'Estado de origem', ondelete='restrict')
    estado_destino_id = fields.Many2one('sped.estado', 'Estado de destino', ondelete='restrict')
    data_inicio = fields.Date('Início', required=True)
    al_icms_proprio_id = fields.Many2one('sped.aliquota.icms.proprio', 'ICMS próprio', required=True)
    al_icms_st_id = fields.Many2one('sped.aliquota.icms.st', 'ICMS ST')
    infadic = fields.Text('Informações adicionais')

    @api.one
    @api.depends('estado_origem_id', 'estado_destino_id')
    def _interna(self):
        self.interna = self.estado_origem_id.uf == self.estado_destino_id.uf

    interna = fields.Boolean(string='Interna', compute=_interna, store=True)


class ProtocoloICMSNCM(models.Model):
    _description = 'Protocolo ICMS - NCM e MVA'
    _name = 'sped.protocolo.icms.ncm'
    #_rec_name = 'descricao'
    _order = 'protocolo_id, ncm_id'

    protocolo_id = fields.Many2one('sped.protocolo.icms', 'Protocolo', require=True, ondelete='cascade')
    ncm_id = fields.Many2one('sped.ncm', 'NCM', required=True)
    mva = fields.Porcentagem('MVA original')
