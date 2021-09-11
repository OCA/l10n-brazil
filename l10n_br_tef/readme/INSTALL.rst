1. Baixar o arquivo: https://drive.google.com/file/d/1k9K30jYBRmBmYo4Bbz5Cm_wDC2kNx-x3/view
2. Descompactar e pasta e mover a pasta TEF para a raiz do sistema /

    $ sudo mv TEF /

3. Dar permissão de escrita para a pasta do java

    $ chmod 777 /TEF/Java -R

4. Acessar a pasta do cliente e dar permissão de execução ao arquivo:

    $ cd '/TEF/V$Pague/Client'
    $ chmod +x V\$PagueClient.bsh

5. Criar link simbólico para o dispositivo PinPad

    $ sudo ln -s /dev/ttyACM0 /dev/ttyUSB

6. Dar Permissão para o dispositivo

    $ sudo chmod 777 /dev/ttyUSB

7. Alterar permissões da pasta /var/lock

    $ sudo chmod 777 /var/lock -R

8. Verficar se no arquivo V\$PagueClient.bsh os dados do servidor e porta estão corretos:

    $ VSPAGUE_SERVER_HOST=187.55.218.195
    $ VSPAGUE_SERVER_PORT=60400

9. Executar o Cliente

    $ sudo ./V\$PagueClient.bsh

10. O seu mac e hostname deve estar cadastrado corretamente no servidor

    $ ifconfig

11. Testar a conexão

    $ telnet localhost 60906
