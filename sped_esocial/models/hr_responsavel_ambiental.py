# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _

IDE_OC = [
    (1, 'Conselho Regional de Medicina (CRM)'),
    (4, 'Conselho Regional de Engenharia e Agronomia (CREA)'),
    (9, 'Outros'),
]

UF = [
    ('AC', 'Acre'),
    ('AL', 'Alagoas'),
    ('AP', 'Amapá'),
    ('AM', 'Amazonas'),
    ('BA', 'Bahia'),
    ('CE', 'Ceará'),
    ('DF', 'Distrito Federal'),
    ('ES', 'Espírito Santo'),
    ('GO', 'Goiás'),
    ('MA', 'Maranhão'),
    ('MT', 'Mato Grosso'),
    ('MS', 'Mato Grosso do Sul'),
    ('MG', 'Minas Gerais'),
    ('PA', 'Pará'),
    ('PB', 'Paraíba'),
    ('PR', 'Paraná'),
    ('PE', 'Pernambuco'),
    ('PI', 'Piauí'),
    ('RJ', 'Rio de Janeiro'),
    ('RN', 'Rio Grando do Norte'),
    ('RS', 'Rio Grando do Sul'),
    ('RO', 'Rondônioa'),
    ('RR', 'Roraima'),
    ('SC', 'Santa Catarina'),
    ('SP', 'São Paulo'),
    ('SE', 'Sergipe'),
    ('TO', 'Tocantins'),
]


class HrResponsavelAmbiente(models.Model):
    _name = 'hr.responsavel.ambiente'
    _description = u'Responsável Pelos Registros Ambientáis'
    _sql_constraints = [
        ('cpf_responsavel_num_inscricao',
         'unique(cpf_responsavel, num_inscricao)',
         'Este responsável já possuí um cadastro nesta organização!'
         )
    ]

    name = fields.Char(
        compute='_compute_name'
    )
    cpf_responsavel = fields.Char(
        string=u'CPF',
        size=11,
    )
    nis_responsavel = fields.Char(
        string=u'NIS',
        size=11,
    )
    nome = fields.Char(
        string=u'Nome',
        size=70,
    )
    identificacao_ordem_classe = fields.Selection(
        string=u'Órgão de classe',
        selection=IDE_OC,
    )
    descricao_ordem_classe = fields.Char(
        string=u'Descrição do Órgão de Classe',
        size=20,
    )
    num_inscricao = fields.Char(
        string=u'Número Inscrição',
        size=14,
    )
    uf = fields.Selection(
        string=u'Unidade Federativa',
        selection=UF,
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            record.name = '{} - Inscrição: {}'.format(
                record.nome, record.num_inscricao)
