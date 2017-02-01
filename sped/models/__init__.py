# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

#
# Cópia de views
#
from inherited_ir_ui_view import *

#
# Model Base
#
from sped_base import *

#
# Tabelas Geográficas
#
from sped_pais import *
from sped_estado import *
from sped_municipio import *

#
# Cadastros básicos
#
from sped_participante import *
from sped_empresa import *
from inherited_res_partner import *

#
# Unidade é requisito para NCM e produtos
#
from sped_unidade import *
from inherited_product_uom import *

#
# Alíquotas
#
from sped_aliquota_icms_proprio import *
from sped_aliquota_icms_st import *
from sped_aliquota_ipi import *
from sped_aliquota_pis_cofins import *
from sped_aliquota_simples import *

#
# Tabelas Fiscais
#
from sped_cest import *
from sped_cfop import *
from sped_cnae import *
from sped_ncm import *
from sped_servico import *
from sped_nbs import *
from sped_ibptax import *
from sped_ncm_cest import *
from sped_ncm_ibptax import *

from sped_aliquota_iss import *
from sped_protocolo_icms import *
from sped_ncm_protocolo import *

from sped_certificado import *

from sped_produto import *
from inherited_product_template import *
from inherited_product_product import *

#
# Fiscal e faturamento
#
from sped_natureza_operacao import *
from sped_operacao import *
from sped_operacao_item import *
from sped_veiculo import *
from sped_documento import *
from sped_documento_item import *
from sped_documento_volume import *
from sped_documento_duplicata import *
