# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Hugo Borges <hugo.borges@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import models, fields, api

ACAO_MANIFESTACAO = [
    ('ciencia', 'Declarar Ciência da Operação'),
    ('confirmar', 'Confirmar Operação'),
    ('desconhecer', 'Desconhecer Operação'),
    ('nao_realizada', 'Operação Não Realizada'),
    ('importa_nfe', 'Importar NF-e'),
    ('salva_xml', 'Salvar XML da NF-e'),
]

class WizardConfirmaAcao(models.TransientModel):
    _name = 'wizard.confirma.acao'
    _description = 'Confirmação de Ações'

    manifestacao_ids = fields.Many2many(
        comodel_name='sped.manifestacao.destinatario',
        string='Manifestações',
    )

    ciencia = fields.Boolean(
        string='Declarar Ciência Automaticamente',
        help='As manifestações cujos estados forem "Pendente" terão sua '
             'Ciência da Emissão declaradas automaticamente.'
             'Caso isso não seja feito, as manifestações em estado pendente '
             'serão ignoradas.',
        default=True,
    )

    state = fields.Selection(
        string=u'Ação a ser feita',
        selection=ACAO_MANIFESTACAO,
        required=True,
        select=True,
    )

    def action_confirma_acao(self):

        if self.state == 'ciencia':
            return self.manifestacao_ids.action_ciencia_emissao()
        else:
            manifestacao_ciente_ids = self.manifestacao_ids

            if self.ciencia:
                #Declara Ciência da emissão nos manifestos ainda pendentes
                for manifestacao_id in self.manifestacao_ids:
                    if manifestacao_id.state == 'pendente':
                        manifestacao_id.action_ciencia_emissao()
            else:
                #Retira as manifestacoes pendentes da lista que será processada
                manifestacao_ciente_ids -= \
                    self.env['sped.manifestacao.destinatario'].\
                        search([('state', '=', 'pendente')])

            if self.state == 'importa_nfe':
                return manifestacao_ciente_ids.action_importa_xmls()

            elif self.state == 'salva_xml':
                return manifestacao_ciente_ids.action_download_xmls()

            elif self.state == 'confirmar':
                return manifestacao_ciente_ids.action_confirmar_operacacao()

            elif self.state == 'desconhecer':
                return manifestacao_ciente_ids.action_operacao_desconhecida()

            elif self.state == 'nao_realizada':
                return manifestacao_ciente_ids.action_negar_operacao()
