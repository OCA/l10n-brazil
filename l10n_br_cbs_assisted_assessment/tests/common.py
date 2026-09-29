# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

CLIENT_CLASS = (
    "odoo.addons.l10n_br_cbs_assisted_assessment.models.receita_integra_rtc"
    ".ReceitaIntegraRtc"
)

# Answer of the debits endpoint, from the official documentation.
DEBITS_FILE = {
    "tiqueteSolicitacao": "692b7b25-44cb-4415-8625-2b9522dd7933.B5E08D55",
    "ni": "00409834",
    "niConsumidor": "20182807000131",
    "geradoEm": "2026-08-19T21:08:32Z",
    "apuracao": [
        {
            "pa": "06/2026",
            "debitos": [
                {
                    "origem": 0,
                    "documento": 55,
                    "chave": "36662749229766700825725366193706115810782882",
                    "emissao": "2026-06-03T04:53:58Z",
                    "registro": "2026-08-13T21:19:16.190202Z",
                    "atualizacao": "2026-08-13T21:19:16.190202Z",
                    "cbs": {
                        "apurado": 80,
                        "excedente": 0,
                        "inexigivel": 0,
                        "suspenso": 0,
                        "extinto": 0,
                        "saldoDevedor": 80,
                    },
                }
            ],
        },
        {
            "pa": "08/2026",
            "debitos": [
                {
                    "origem": 0,
                    "documento": 55,
                    "chave": "36662749229766700825725366193706115810782883",
                    "emissao": "2026-08-13T04:53:56Z",
                    "registro": "2026-08-14T12:40:16.763258Z",
                    "atualizacao": "2026-08-14T12:40:16.763258Z",
                    "cbs": {
                        "apurado": 40,
                        "excedente": 0,
                        "inexigivel": 0,
                        "suspenso": 0,
                        "extinto": 0,
                        "saldoDevedor": 40,
                    },
                }
            ],
        },
    ],
}

# Answer of the credits endpoint, from the official documentation.
CREDITS_FILE = {
    "tiqueteSolicitacao": "692b7b25-44cb-4415-8625-2b9522dd7933.B5E08D55",
    "ni": "12345678",
    "niConsumidor": "12345678",
    "geradoEm": "2026-08-26T16:00:00Z",
    "apuracao": [
        {
            "pa": "08/2026",
            "creditos": [
                {
                    "origem": 1,
                    "documento": 55,
                    "chave": "36662749229766700825725366193706115810782884",
                    "emissao": "2026-08-01T00:00:00Z",
                    "registro": "2026-08-01T00:00:00Z",
                    "atualizacao": "2026-08-01T00:00:00Z",
                    "cbs": {
                        "apurado": 15,
                        "excedentes": 0,
                        "apropriacao": {
                            "inapropriavel": 0,
                            "suspenso": 3,
                            "prescrito": 0,
                            "aApropriar": 0,
                            "apropriado": 12,
                            "utilizacao": {
                                "inutilizavel": 0,
                                "utilizado": 5,
                                "restabelecido": 0,
                                "naoUtilizado": {
                                    "saldoCredor": 7,
                                    "pedidoRessarcimento": 0,
                                },
                            },
                        },
                    },
                }
            ],
        }
    ],
}
