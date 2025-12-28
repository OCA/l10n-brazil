## Compatibilidade entre a Localização Brasil OCA e o Módulo l10n_br "oficial"

Este módulo harmoniza o módulo base da localização brasileira da OCA, `l10n_br_base`, com o módulo `l10n_br`, módulo da Odoo Community que também serve como base para a localização Odoo Enterprise. Sua finalidade é abrir o rico e maduro ecossistema open source da OCA para o ambiente mais limitado do Odoo Enterprise, compatibilizando ambos os mundos.

### Benefícios e Funcionalidades:

*   **Integração de Ecossistemas:** Conecta a abrangência e flexibilidade do desenvolvimento colaborativo da OCA com a base do Odoo Enterprise. Isso permite que os módulos Enterprise sejam enriquecidos com uma parcela significativa das funcionalidades da localização OCA. Este módulo funciona porque foi previamente feito um trabalho de harmonização dos campos dos objetos `res.partner` e `res.company` na OCA com os novos nomes introduzidos pela Odoo a partir das versões 16.0/17.0/18.0.
*   **Compatibilidade Estendida:** Ao resolver os conflitos entre `l10n_br_base` (e aproximadamente um terço dos módulos OCA que dependem dele) e o módulo `l10n_br`, este módulo viabiliza o uso de aproximadamente um terço dos módulos da localização OCA com a localização fechada do Odoo Enterprise.
*   **Prevenção de Conflitos:** Sua função é desativar as views conflitantes de `res.partner` e `res.company` do módulo `l10n_br`. Isso elimina a duplicação de campos na interface, priorizando as visões mais completas e robustas fornecidas pelo `l10n_br_base` da OCA. O módulo também evita a duplicação dos registros de cidades `res.city`.

### Público-Alvo e Recomendações:

*   **Para usuários do Odoo Enterprise:** Este módulo é ideal para uma **transição progressiva para a OCA** ou para projetos que necessitam de funcionalidades de ambos os conjuntos de módulos.
*   **Para usuários exclusivos da OCA:** Se você já utiliza apenas a localização open source OCA (**parabéns!**), a instalação deste módulo **não é recomendada**. Os módulos `l10n_br` e `l10n_br_base_l10n_br_compat` não agregam valor ao seu projeto e podem introduzir complexidade desnecessária.

### Nota Técnica Importante:
A compatibilidade remove o campo `l10n_latam_identification_type_id`. Caso este campo seja essencial para a sua operação (ex.: em um contexto multi-empresa com outros países da América Latina), será necessário recriá-lo através de um módulo de customização específico.

### Aviso Importante sobre Compatibilidade de Licenças:

É fundamental entender as implicações das licenças envolvidas ao integrar módulos de ecossistemas diferentes:

*   **Licença AGPL (Módulos OCA):** A licença AGPL-3, sob a qual a grande maioria dos módulos da OCA é publicada (e que era a licença original do Odoo), é uma licença de *copyleft* forte. Ela garante a sua liberdade de usar, modificar e redistribuir o software, mas **exige que qualquer trabalho derivado (módulo customizado que dependa de um módulo AGPL) seja também licenciado sob a AGPL** quando distribuído ou oferecido como serviço (SaaS). O objetivo é garantir que as melhorias feitas no software permaneçam livres e abertas para toda a comunidade.

*   **Licença Proprietária (Odoo Enterprise):** A licença do Odoo Enterprise é restritiva e proprietária. Ela **não permite a redistribuição ou publicação do código-fonte** dos módulos Enterprise ou de trabalhos derivados deles.

**O Conflito Fundamental:**
As liberdades fundamentais garantidas pela AGPL são **incompatíveis** com as restrições impostas pela licença proprietária do Enterprise. Portanto, **é juridicamente impossível criar um módulo único que dependa simultaneamente de um módulo OCA (AGPL) e de um módulo Odoo Enterprise (proprietário) e depois redistribuí-lo** (mesmo por SaaS), pois isso violaria os termos de uma ou de outra licença.

**Como este módulo resolve isso?**
Este módulo de compatibilidade é licenciado sob a AGPL e depende *apenas* do módulo `l10n_br` (também AGPL) da Odoo Community e do `l10n_br_base` (AGPL) da OCA. Ele não toca em nenhum código Enterprise. Sua função é criar um *ambiente* onde os módulos Enterprise (executados sob sua própria licença) e os módulos OCA (executados sob a AGPL) possam coexistir tecnicamente em uma mesma instância Odoo, desde que o usuário possua licenças válidas para ambos. A responsabilidade de cumprir os termos de ambas as licenças recai sobre a empresa que os utiliza em conjunto.
