# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from . import inherited_mail_compose_message
from . import inherited_mail_template


from . import sped_certificado
from . import inherited_sped_empresa
from . import inherited_sped_operacao

from . import inherited_sped_documento
from . import inherited_sped_documento_item
from . import inherited_sped_documento_pagamento
from . import inherited_sped_documento_duplicata
from . import sped_documento_carta_correcao
from . import sped_manifestacao_destinatario
from . import sped_consulta_dfe
from . import sped_importa_nfe

#
# Montagem do xml
#
from .monta_nfe import *

#
# Leitura do xml
#
from .le_nfe import *

