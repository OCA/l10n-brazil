# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Danimar Ribeiro 26/06/2013                              #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp.osv import orm
from openerp.tools.translate import _


def validate_nfe_invalidate_number(company, record):
    error = u'As seguintes configurações estão faltando:\n'
    if not company.partner_id or not company.partner_id.l10n_br_city_id \
            or not company.partner_id.l10n_br_city_id.state_id or not \
            company.partner_id.l10n_br_city_id.state_id.code:
        error += u'Código do estado no endereço da empresa\n'
    if not company.nfe_version:
        error += u'Versão da NFe na configuração da empresa\n'
    if not company.partner_id.cnpj_cpf:
        error += u'CNPJ na configuração da empresa\n'
    if not record.document_serie_id.code:
        error += u'Série no registro de inutilização\n'
    if not record.number_start:
        error += u'Número de inicio no registro de inutilização\n'
    if not record.number_end:
        error += u'Número final no registro de inutilização\n'
    if error != u'As seguintes configurações estão faltando:\n':
        raise orm.except_orm(_(u'Validação !'), _(error))


def validate_invoice_cancel(invoice):
    error = u'Verifique os problemas com o cancelamento:\n'
    if not invoice.nfe_access_key:
        error += u'Nota Fiscal - Chave de acesso NF-e\n'
    if not invoice.nfe_status:
        error += u'Empresa - Protocolo de autorização na Sefaz\n'
    if error != u'Verifique os problemas com o cancelamento:\n':
        raise orm.except_orm(_(u'Validação !'), _(error))


def validate_nfe_configuration(company):
    error = u'As seguintes configurações estão faltando:\n'
    if not company.nfe_version:
        error += u'Empresa - Versão NF-e\n'
    if not company.nfe_a1_file:
        error += u'Empresa - Arquivo NF-e A1\n'
    if not company.nfe_a1_password:
        error += u'Empresa - Senha NF-e A1\n'
    if error != u'As seguintes configurações estão faltando:\n':
        raise orm.except_orm(_(u'Validação !'), _(error))
