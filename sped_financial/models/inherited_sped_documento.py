# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class SpedDocumento(models.Model):

    _inherit = 'sped.documento'

    def _get_financial_ids(self):
        document_id = self._name + ',' + str(self.id)
        self.financial_ids = self.env['financial.move'].search(
            [['doc_source_id', '=', document_id]]
        )

    financial_ids = fields.One2many(
        comodel_name='financial.move',
        compute='_get_financial_ids',
        string=u'Financial Items',
        readonly=True,
        copy=False
    )

    def _prepara_lancamento_item(self, item):
        return {
            'document_number':
                "{0.serie}-{0.numero:0.0f}-{1.numero}/{2}".format(
                    self, item, len(self.duplicata_ids)),
            'date_maturity': item.data_vencimento,
            'amount': item.valor
        }

    def _prepara_lancamento_financeiro(self):
        return {
            'date': self.data_emissao,
            'financial_type': '2receive',
            'partner_id':
                self.participante_id and self.participante_id.partner_id.id,
            'doc_source_id': self._name + ',' + str(self.id),
            'bank_id': 1,
            'company_id': self.empresa_id and self.empresa_id.company_id.id,
            'currency_id': self.currency_id.id,
            'payment_term_id':
                self.payment_term_id and self.payment_term_id.id or False,
            # 'account_type_id':
            # 'analytic_account_id':
            # 'payment_mode_id:
            'lines': [self._prepara_lancamento_item(parcela)
                      for parcela in self.duplicata_ids],
        }

    def action_financial_create(self):
        """ Cria o lançamento financeiro do documento fiscal
        :return:
        """
        p = self._prepara_lancamento_financeiro()
        financial_move_ids = self.env['financial.move']._create_from_dict(p)
        financial_move_ids.action_confirm()

    def executa_depois_autorizar(self):
        super(SpedDocumento, self).executa_depois_autorizar()
        self.action_financial_create()
