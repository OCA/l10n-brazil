# The batch envelope and the receipt query are NOT imported here on purpose:
# they are other schema families and Reinf, TStatus and TArquivoReinf would
# collide with the event models. See readme/ROADMAP.md.

# Periodic and table events
from . import r_1000_evt_info_contribuinte_v2_01_02
from . import r_1050_evt1050_tab_lig_v2_01_02
from . import r_1070_evt_tab_processo_v2_01_02
from . import r_2010_evt_tomador_servicos_v2_01_02
from . import r_2020_evt_prestador_servicos_v2_01_02
from . import r_2030_evt_recurso_recebido_associacao_v2_01_02
from . import r_2040_evt_recurso_repassado_associacao_v2_01_02
from . import r_2050_evt_info_prod_rural_v2_01_02
from . import r_2055_evt2055_aquisicao_prod_rural_v2_01_02
from . import r_2060_evt_info_cprb_v2_01_02
from . import r_2098_evt_reabre_ev_per_v2_01_02
from . import r_2099_evt_fechamento_v2_01_02
from . import r_3010_evt_esp_desportivo_v2_01_02
from . import r_4010_evt4010_pagto_beneficiario_pf_v2_01_02
from . import r_4020_evt4020_pagto_beneficiario_pj_v2_01_02
from . import r_4040_evt4040_pagto_benef_nao_identificado_v2_01_02
from . import r_4080_evt4080_retencao_recebimento_v2_01_02
from . import r_4099_evt4099_fechamento_dirf_v2_01_02
from . import r_9000_evt_exclusao_v2_01_02

# Totalizer events, returned by the tax authority
from . import retorno_r_9001_evt_total_v2_01_02
from . import retorno_r_9005_evt_ret_v2_01_02
from . import retorno_r_9011_evt_total_contrib_v2_01_02
from . import retorno_r_9015_evt_ret_cons_v2_01_02
