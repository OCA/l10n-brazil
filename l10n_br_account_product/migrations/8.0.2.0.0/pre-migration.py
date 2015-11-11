# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2015  Renato Lima - Akretion
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

# TODO
# Migration
# =========

# - Rename columns tax_id to tax_template_id and tax_code_id to
#   tax_code_template_id in l10n_br_tax.definition.sale.template
# - Rename columns tax_id to tax_template_id and tax_code_id to
#   tax_code_template_id in l10n_br_tax.definition.purchase.template
# - Replace ncm_id to fiscal_classification_id in product.template object
# - replace ncm_id to fiscal_classification_id in
#   account.fiscal.position.tax.template object
# - replace ncm_id to fiscal_classification_id in account.fiscal.position.tax
# - Drop table l10n_br_tax_definition_template
# - Drop table l10n_br_tax_definition
