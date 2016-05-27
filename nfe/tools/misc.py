# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2016  Renato Lima - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

import os

from openerp.tools import config
from openerp.tools.translate import _
from openerp.exceptions import RedirectWarning
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm


def mount_path_nfe(company, document='nfe'):
    db_name = company._cr.dbname
    cnpj = punctuation_rm(company.cnpj_cpf)

    filestore = config.filestore(db_name)
    nfe_path = '/'.join([filestore, 'PySPED', document, cnpj])
    if not os.path.exists(nfe_path):
        try:
            os.makedirs(nfe_path)
        except OSError:
            raise RedirectWarning(
                _(u'Erro!'),
                _(u"""Verifique as permissões de escrita
                    e o caminho da pasta"""))
    return nfe_path
