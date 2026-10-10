Os controles do mock são visíveis apenas para gerentes fiscais e atuam sobre
a empresa ativa.

No topo da lista **Fiscal › Consultas DF-e › NF-e de Terceiros**:

- **Consultar NF-e**: dispara a distribuição DF-e de NF-e da empresa.
- **Alternar Mock**: liga ou desliga o modo mock da empresa (também
  disponível no campo *Modo Mock DF-e* da aba DF-e da empresa).
- **Resetar Cooldown**: limpa o intervalo de espera entre
  consultas imposto após cada resposta da SEFAZ.

No menu **Fiscal › Consultas DF-e › Mock**:

- **Gerar NSU Mock**: cria resumos (resNFe), NF-e completas (procNFe) e
  eventos no pool local de NSUs.
- **Pool de NSU Mock**: lista os NSUs gerados e permite resetar os consumidos.

Com o modo mock ligado, manifestar *Ciência da Operação* em um resumo gera a
NF-e completa correspondente no pool, que chega na consulta seguinte.
