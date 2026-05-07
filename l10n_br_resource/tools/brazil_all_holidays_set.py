import re

from workalendar.america import Brazil, BrazilBankCalendar
from workalendar.america.brazil import IBGE_REGISTER


class BrazilianHoliday:
    def __init__(self, nome, data, estado_ibge, municipio_ibge, abrangencia, tipo):
        self.estado_ibge = estado_ibge
        self.municipio_ibge = municipio_ibge
        self.municipio_nome = ""
        self.abrangencia = abrangencia
        self.tipo = tipo
        self.nome = nome
        self.data = data


# Commemorative holidays list
COMMEMORATIVE_HOLIDAYS = [
    "Consciência Negra",
]


def brazil_all_holidays_set(year):
    """Returns all holidays in brazil
    with their respective type and coverage"""

    holidays_set = []

    # Get brazilian national holidays
    cal = Brazil()
    for national_holidays in cal.holidays(year):
        holiday_name = national_holidays[1]
        holiday_date = national_holidays[0]

        if national_holidays[1] in COMMEMORATIVE_HOLIDAYS:
            tipo_feriado = "C"
        else:
            tipo_feriado = "F"
        holiday_obj = BrazilianHoliday(
            holiday_name, holiday_date, None, None, "N", tipo_feriado
        )
        if not any(x.nome == holiday_obj.nome for x in holidays_set):
            holidays_set.append(holiday_obj)

    # Get brazilian bank holidays
    cal = BrazilBankCalendar()
    for bank_holidays in cal.holidays(year):
        holiday_name = bank_holidays[1]
        holiday_date = bank_holidays[0]

        holiday_obj = BrazilianHoliday(holiday_name, holiday_date, None, None, "N", "B")
        if not any(x.nome == holiday_obj.nome for x in holidays_set):
            holidays_set.append(holiday_obj)

    # Get holidays from brazilian state
    for register in IBGE_REGISTER.items():
        estado_ibge = re.sub("BR-IBGE-", "", register[0])
        if len(estado_ibge) == 2:
            cal_state = IBGE_REGISTER[register[0]]()
            for state_holidays in cal_state.holidays(year):
                holiday_name = state_holidays[1]
                holiday_date = state_holidays[0]

                holiday_obj = BrazilianHoliday(
                    holiday_name, holiday_date, estado_ibge, None, "E", "F"
                )

                # Check if is just a state holiday
                if not any(
                    (x.nome == holiday_obj.nome and not x.estado_ibge)
                    for x in holidays_set
                ):
                    holidays_set.append(holiday_obj)

    # Get brazilian municipal holidays
    for register in IBGE_REGISTER.items():
        municipio_ibge = re.sub("BR-IBGE-", "", register[0])
        estado_ibge = municipio_ibge[0:2]
        if len(municipio_ibge) > 2:
            cal_city = IBGE_REGISTER[register[0]]()

            for city_holiday in cal_city.holidays(year):
                holiday_name = city_holiday[1]
                holiday_date = city_holiday[0]

                holiday_obj = BrazilianHoliday(
                    holiday_name, holiday_date, estado_ibge, municipio_ibge, "M", "F"
                )

                # Check if is just a municipal holiday
                if not any(
                    (x.nome == holiday_obj.nome and not x.municipio_ibge)
                    for x in holidays_set
                ):
                    holidays_set.append(holiday_obj)
    return holidays_set
