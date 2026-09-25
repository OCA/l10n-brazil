Os mixins de `wsdl` e `soap` não fazem parte deste módulo, porque a transmissão
ao webservice ainda não está implementada.

O modelo de obrigação de recolhimento é genérico o bastante para servir outros
tributos (DARF, DAS, GARE), mas nasce específico da GNRE por decisão consciente.
A promoção para um modelo compartilhado deve acontecer quando existir um segundo
consumidor real, por extração de mixin.

Há um `# noqa: E501` em `config_uf_v1_00.py`: o `_binding_type` de uma classe
aninhada profunda passa de 88 caracteres e o gerador não quebra a linha. Some
quando o xsdata-odoo aprender a quebrar, e por isso não vale corrigir à mão a
cada regeração.
