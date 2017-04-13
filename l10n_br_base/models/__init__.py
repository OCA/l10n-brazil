# -*- coding: utf-8 -*-
#
# Copyright (C) 2015  Renato Lima - Akretion
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#

#
# Sincronização de casas decimais
#
from . import inherited_decimal_precision
from . import inherited_res_currency

#
# Model Base
#
from . import sped_base

#
# Tabelas Geográficas
#
from . import sped_pais
from . import sped_estado
from . import sped_municipio

#
# Tabelas Fiscais
#
from . import sped_cnae

#
# Cadastros básicos
#
from . import sped_participante
from . import inherited_res_company
from . import inherited_res_partner
from . import sped_empresa
