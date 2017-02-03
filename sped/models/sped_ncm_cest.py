# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models


class NCM(models.Model):
    _name = 'sped.ncm'
    _inherit = 'sped.ncm'

    cest_ids = fields.Many2many(
        comodel_name='sped.cest',
        relation='sped_ncm_cest',
        column1='ncm_id',
        column2='cest_id',
        string=u'Códigos CEST'
    )


class CEST(models.Model):
    _name = 'sped.cest'
    _inherit = 'sped.cest'

    ncm_ids = fields.Many2many(
        comodel_name='sped.ncm',
        relation='sped_ncm_cest',
        column1='cest_id',
        column2='ncm_id',
        string=u'NCMs'
    )
    ncm_permitido = fields.Char(
        string=u'NCMs permitidos',
        size=200,
        help='Informe a lista de NCMs permitidos, sem pontos, separados por |'
    )

    @api.constrains('ncm_permitido')
    @api.depends('ncm_permitido')
    def _onchange_ncm_permitido(self):
        ncm_pool = self.env['sped.ncm']

        for cest in self:
            if not cest.ncm_permitido:
                continue

            if '|' in cest.ncm_permitido:
                lista_ncms = cest.ncm_permitido.split('|')
            else:
                lista_ncms = [cest.ncm_permitido]

            ncm_ids = []
            for codigo_ncm in lista_ncms:
                codigo_ncm = codigo_ncm.strip()

                if len(codigo_ncm) > 8:
                    codigo_ncm = codigo_ncm[:8]

                ncms = ncm_pool.search([
                    ('codigo', '=ilike', codigo_ncm + '%')
                ])

                ncm_ids += [ncm.id for ncm in ncms]

            cest.write({'ncm_ids': [[6, cest.id, ncm_ids]]})
