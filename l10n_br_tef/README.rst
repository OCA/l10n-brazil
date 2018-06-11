POS Payment Terminal
====================

O módulo oferece para o terminal de pagamento do POS opções de
uso de cartão de crédito e cartão de débito.

Integrando a localização brasileira, o módulo foi desenvolvido em
2018 pela KMEE Informática.

Instalação
==========

1. Baixar o arquivo

     https://drive.google.com/file/d/1k9K30jYBRmBmYo4Bbz5Cm_wDC2kNx-x3/view


2. Descompactar e pasta e mover a pasta TEF para a raiz do sistema /

    sudo mv TEF /

3. Dar permissão de escrita para a pasta do java

    chmod 777 /TEF/Java -R

4. Acessar a pasta do cliente e dar permissão de execução ao arquivo:

    cd '/TEF/V$Pague/Client'

    chmod +x V\$PagueClient.bsh

5. Criar link simbólico para o dispositivo PinPad

    sudo ln -s /dev/ttyACM0 /dev/ttyUSB

6. Dar Permissão para o dispositivo

    sudo chmod 777 /dev/ttyUSB

7. Alterar permissões da pasta /var/lock

    sudo chmod 777 /var/lock -R


8. Verficar se no arquivo V\$PagueClient.bsh os dados do servidor e porta
estão corretos:

        VSPAGUE_SERVER_HOST=187.55.218.195

        VSPAGUE_SERVER_PORT=60400


9. Executar o Cliente

    sudo ./V\$PagueClient.bsh

10. O seu mac e hostname deve estar cadastrado corretamente no servidor

    ifconfig

11. Testar a conexão

    telnet localhost 60906


Configuração
============

É suportado dois tipos de pagamento nesse módulo, cartão de crédito
ou cartão de débito.

Para que o TEF funcione, é necessário habilitar o checkbox 'TEF', dentro das configurações do Ponto de Vendas.

Essa configuração pode ser acessada em: **Ponto de Venda -> Configuração -> Ponto de Vendas.**

Selecione o ponto de venda a ser utilizado e, em 'Hardware Proxy', habilite o checkbox **TEF**.

Uso
===

É possível pela interface do POS selecionar a forma como será feita o
pagamento. Assim, escolhido cartão, pode-se escolher entre crédito ou
débito. Após esse passo, acontece o processamento e é retornada uma
resposta.

Créditos
========

Contribuidores
--------------

* Hugo Uchôas Borges <hugo.borges@kmee.com.br>
* Átilla Graciano da Silva <atilla.silva@kmee.com.br>
* Bianca da Rocha Bartolomei <bianca.bartolomei@kmee.com.br>
