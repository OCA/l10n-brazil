# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE - Átila Graciano <atilla.silva@kmee.com.br>
# Copyright 2017 KMEE - Bianca Bartolomei <bianca.bartolomei@kmee.com.br>
# Copyright 2017 KMEE - Wagner Pereira <wagner.pereira@kmee.com.br>
# Copyright 2018 ABGF - Wagner Pereira <wagner.pereira@abgf.gov.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Tabelas SPED Gerais',
    'summary': """
        Implementa as tabelas fixas do SPED (e-Social e EFD/REINF)
        """,
    'version': '8.0.0.1.0',
    'category': 'Hidden',
    'license': 'AGPL-3',
    'author': 'KMEE & ABGF',
    'website': 'www.odoobrasil.org.br, www.abgf.gov.br',
    'depends': ['l10n_br_hr'],
    'external_dependencies': {
        'python': [
            'pybrasil',
        ],
    },
    'data': [
        # Segurança
        'security/security.xml',
        'security/ir.model.access.csv',

        # Menu base
        'views/menus.xml',

        # Tabelas
        'views/classificacao_servico.xml',
        'views/classificacao_tributaria.xml',
        'views/codigo_aliquota_FPAS.xml',
        'views/categoria_trabalhador.xml',
        'views/financiamento_aposentadoria.xml',
        'views/natureza_rubrica.xml',
        'views/parte_corpo.xml',
        'views/pais.xml',
        'views/tipo_inscricao.xml',
        'views/agente_causador.xml',
        'views/situacao_geradora_doenca.xml',
        'views/situacao_geradora_acidente.xml',
        'views/natureza_lesao.xml',
        'views/tipo_dependente.xml',
        'views/tipo_lotacao_tributaria.xml',
        'views/motivo_afastamento.xml',
        'views/motivo_desligamento.xml',
        'views/tipo_logradouro.xml',
        'views/natureza_juridica.xml',
        'views/motivo_cessacao.xml',
        'views/tipo_beneficio.xml',
        'views/codificacao_acidente_trabalho.xml',
        'views/fatores_meio_ambiente.xml',
        'views/procedimentos_diagnosticos.xml',
        'views/atividades_perigosas_insalubres.xml',
        'views/treinamentos_capacitacoes.xml',

        # Data
        'data/classificacao_servico.xml',
        'data/classificacao_tributaria.xml',
        'data/natureza_lesao.xml',
        'data/tipo_lotacao_tributaria.xml',
        'data/categoria_trabalhador.xml',
        'data/financiamento_aposentadoria.xml',
        'data/natureza_rubrica.xml',
        'data/tipo_dependente.xml',
        'data/parte_corpo.xml',
        'data/pais.xml',
        'data/tipo_inscricao.xml',
        'data/agente_causador.xml',
        'data/situacao_geradora_doenca.xml',
        'data/situacao_geradora_acidente.xml',
        'data/natureza_lesao.xml',
        'data/motivo_afastamento.xml',
        'data/motivo_desligamento.xml',
        'data/tipo_logradouro.xml',
        'data/natureza_juridica.xml',
        'data/motivo_cessacao.xml',
        'data/tipo_beneficio.xml',
        'data/codificacao_acidente_trabalho.xml',
        'data/fatores_meio_ambiente.xml',
        'data/codigo_aliquota_FPAS.xml',
        'data/sped.procedimentos_diagnosticos.csv',
        'data/sped.atividades_perigosas_insalubres.csv',
        'data/sped.treinamentos_capacitacoes.csv',
    ],
    'application': True,
}
