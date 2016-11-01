# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from pybrasil.data import parse_datetime
from pybrasil.valor.decimal import Decimal as D


class IBPTax(models.Model):
    _description = 'IBPTax'
    _name = 'sped.ibptax'
    _order = 'estado_id'
    _rec_name = 'estado_id'

    estado_id = fields.Many2one('sped.estado', 'Estado')
    versao = fields.Char('Versão', size=20)
    data_validade = fields.Date('Válida até')
    ncm_ids = fields.One2many('sped.ibptax.ncm', 'ibptax_id', 'NCMs')
    nbs_ids = fields.One2many('sped.ibptax.nbs', 'ibptax_id', 'NBSs')
    servico_ids = fields.One2many('sped.ibptax.servico', 'ibptax_id', 'Serviços')

    @api.one
    def atualizar_tabela(self):
        sped_ncm = self.env['sped.ncm']
        sped_nbs = self.env['sped.nbs']
        sped_servico = self.env['sped.servico']
        sped_icms = self.env['sped.aliquota.icms.proprio']
        sped_estado = self.env['sped.estado']
        ibptax_ncm = self.env['sped.ibptax.ncm']
        ibptax_nbs = self.env['sped.ibptax.nbs']
        ibptax_servico = self.env['sped.ibptax.servico']

        versao = '16.2.A'
        arquivo = '/home/ari/projetos/novo/addons/sistema/data/ibptax/TabelaIBPTax{uf}{versao}.csv'.format(uf=self.estado_id.uf, versao=versao)

        ncm_ids = ibptax_ncm.search([('ibptax_id', '=', self.id)])
        ncm_ids.unlink()

        nbs_ids = ibptax_nbs.search([('ibptax_id', '=', self.id)])
        nbs_ids.unlink()

        servico_ids = ibptax_servico.search([('ibptax_id', '=', self.id)])
        servico_ids.unlink()

        arq = open(arquivo, 'r')

        for linha in arq.readlines():
            codigo, ex, tipo, descricao, nacionalfederal, importadosfederal, estadual, municipal, vigenciainicio, vigenciafim, chave, versao, fonte = linha.decode('iso-8859-1').split(';')

            if tipo == '0':
                if ex:
                    ncm_ids = sped_ncm.search([('codigo', '=', codigo), ('ex', '=', ex)])
                else:
                    ncm_ids = sped_ncm.search([('codigo', '=', codigo), ('ex', '=', False)])

                if len(ncm_ids) == 0:
                    dados = {
                        'codigo': codigo,
                        'ex': ex,
                        'descricao': descricao,
                    }
                    ncm_ids = sped_ncm.create(dados)

                icms_ids = sped_icms.search([('al_icms', '=', D(estadual))])

                dados = {
                    'ibptax_id': self.id,
                    'ncm_id': ncm_ids[0].id,
                    'al_ibpt_nacional': D(nacionalfederal),
                    'al_ibpt_internacional': D(importadosfederal),
                    'al_ibpt_estadual': D(estadual),
                    'al_icms_id': icms_ids[0].id if len(icms_ids) else False,
                }
                ibptax_ncm.create(dados)

            elif tipo == '1':
                nbs_ids = sped_nbs.search([('codigo', '=', codigo)])

                if len(nbs_ids) == 0:
                    dados = {
                        'codigo': codigo,
                        'descricao': descricao,
                    }
                    print('faltou nbs', dados)
                    nbs_ids = sped_nbs.create(dados)

                dados = {
                    'ibptax_id': self.id,
                    'nbs_id': nbs_ids[0].id,
                    'al_ibpt_nacional': D(nacionalfederal),
                    'al_ibpt_internacional': D(importadosfederal),
                    'al_ibpt_municipal': D(municipal),
                }
                print('vai criar', dados)
                ibptax_nbs.create(dados)

            elif tipo == '2' and descricao != 'Vetado':
                servico_ids = sped_servico.search([('codigo', '=', codigo)])

                if len(servico_ids) == 0:
                    dados = {
                        'codigo': codigo,
                        'descricao': descricao,
                    }
                    print('faltou servico', dados)
                    servico_ids = sped_servico.create(dados)

                dados = {
                    'ibptax_id': self.id,
                    'servico_id': servico_ids[0].id,
                    'al_ibpt_nacional': D(nacionalfederal),
                    'al_ibpt_internacional': D(importadosfederal),
                    'al_ibpt_municipal': D(municipal),
                }
                print('vai criar', dados)
                ibptax_servico.create(dados)

        arq.close()
        self.data_validade = str(parse_datetime(vigenciafim))[:10]
        self.versao = versao


class IBPTaxNCM(models.Model):
    _description = 'IBPTax por NCM'
    _name = 'sped.ibptax.ncm'

    ibptax_id = fields.Many2one('sped.ibptax', 'IBPTax', ondelete='cascade')
    estado_id = fields.Many2one('sped.estado', 'Estado', related='ibptax_id.estado_id', store=True)
    ncm_id = fields.Many2one('sped.ncm', 'NCM')
    al_ibpt_nacional = fields.Porcentagem('Nacional')
    al_ibpt_internacional = fields.Porcentagem('Internacional')
    al_ibpt_estadual = fields.Porcentagem('Estadual')
    al_icms_id = fields.Many2one('sped.aliquota.icms.proprio', 'Estadual')


class IBPTaxNBS(models.Model):
    _description = 'IBPTax por NBS'
    _name = 'sped.ibptax.nbs'

    ibptax_id = fields.Many2one('sped.ibptax', 'IBPTax', ondelete='cascade')
    estado_id = fields.Many2one('sped.estado', 'Estado', related='ibptax_id.estado_id', store=True)
    nbs_id = fields.Many2one('sped.nbs', 'NBS')
    al_ibpt_nacional = fields.Porcentagem('Nacional')
    al_ibpt_internacional = fields.Porcentagem('Internacional')
    al_ibpt_municipal = fields.Porcentagem('Municipal')


class IBPTaxServico(models.Model):
    _description = 'IBPTax por Serviço'
    _name = 'sped.ibptax.servico'

    ibptax_id = fields.Many2one('sped.ibptax', 'IBPTax', ondelete='cascade')
    estado_id = fields.Many2one('sped.estado', 'Estado', related='ibptax_id.estado_id', store=True)
    servico_id = fields.Many2one('sped.servico', 'Serviço')
    al_ibpt_nacional = fields.Porcentagem('Nacional')
    al_ibpt_internacional = fields.Porcentagem('Internacional')
    al_ibpt_municipal = fields.Porcentagem('Municipal')
