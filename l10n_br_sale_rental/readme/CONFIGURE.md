1. Em Inventário > Configuração > Armazéns, marque *Rental Allowed* no armazém
   (o `sale_rental` cria os locais e as rotas). Este módulo cria os tipos de
   operação "Rental Delivery" (LOC-REM) e "Rental Return" (LOC-RET) e liga as
   regras de locação às operações fiscais.
2. Nas operações fiscais "Remessa em comodato/locação" e "Entrada de retorno de
   comodato/locação", informe o diário usado para emitir as NF-e a partir das
   transferências.
3. Para usar outras operações, preencha a aba *Rental* do cadastro fiscal da
   empresa (operação do aluguel, da remessa e do retorno).
4. Crie o serviço de aluguel pelo botão *Create Rental Service* do produto: o
   serviço já nasce com tipo fiscal "Serviços" e, se existir na base, com o
   código de tributação nacional 99.01.01 da NFS-e.
