# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class HrContractChangeReason(models.Model):

    _name = 'l10n_br_hr.contract.change_reason'
    _description = u"Motivo de alteração contatual"

    name = fields.Char(u"Motivo")


class HrContractChange(models.Model):

    _name = 'l10n_br_hr.contract.change'
    _description = u"Alteração contatual"
    _inherit = 'hr.contract'

    change_type = fields.Selection(
        selection=[
            ('remuneracao', u'Remuneração'),
            ('jornada', u'Jornada'),
            ('cargo-atividade', u'Cargo/Atividade'),
            ('filiacao-sindical', u'Filiação Sindical'),
            ('lotacao-local', u'Lotação/Local de trabalho'),
            ('reajuste-salarial', u'Reajuste Salarial'),
            ('curso-treinamento', u'Curso/Treinamento'),
        ],
        string=u"Tipo de alteração contratual",
    )
    change_reason_id = fields.Many2One(
        comodel_name='hr.contract.change_reason',
        string=u"Motivo",
    )
    change_date = fields.Date(u'Data da alteração')




