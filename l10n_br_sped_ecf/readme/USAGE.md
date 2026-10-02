Antes da primeira escrituração, configure:

1.  **Signatários** (registro 0930), na empresa: no mínimo o responsável
    legal e o contabilista, que precisa do número de inscrição no CRC.
2.  **Sócios** (registro Y600), na empresa: percentual do capital e o que
    cada um recebeu no ano.
3.  **Natureza da receita na ECF**, em cada conta de receita: é a linha do
    registro P200 em que ela é apurada (receita bruta pelos percentuais de
    presunção, rendimentos de aplicações, juros sobre o capital próprio e
    assim por diante). Conta de receita sem classificação entra em "Demais
    Receitas e Ganhos de Capital", que é o tratamento mais oneroso, e a
    apuração registra o aviso no chatter da declaração.
4.  **Conta referencial da RFB**, em cada conta do plano: é o que alimenta
    os registros J051, K156, K356, P100 e P150. Sem ela, o balanço e a DRE
    em contas referenciais saem vazios.

Depois:

1.  Entre no menu SPED\>ECF e crie uma Declaração do SPED para a empresa e o
    período desejado. Preencha os dados (que são o registro 0000).
2.  Clique no botão "Puxar os registros do Odoo" para popular os registros
    do SPED.
3.  Complete na interface o que o Odoo não tem como saber (atividade
    incentivada, operações com o exterior, livro caixa) ou importe de outro
    arquivo.
4.  Clique no botão "Gerar arquivo do SPED" e baixe o arquivo que foi
    adicionado no chatter. Transmita com o validador da Receita.
