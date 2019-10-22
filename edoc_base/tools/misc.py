# -*- coding: utf-8 -*-
# Copyright (C) 2016  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import os

from odoo.tools import config
from odoo.tools.translate import _
from odoo.exceptions import RedirectWarning
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm


def caminho_empresa(company_id, document):
    db_name = company_id._cr.dbname
    cnpj = punctuation_rm(company_id.cnpj_cpf)

    filestore = config.filestore(db_name)
    path = '/'.join([filestore, 'edoc', document, cnpj])
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            raise RedirectWarning(
                _(u'Erro!'),
                _(u"""Verifique as permissões de escrita
                    e o caminho da pasta"""))
    return path
