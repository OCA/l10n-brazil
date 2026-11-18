import re

from workalendar.america import Brazil, BrazilBankCalendar
from workalendar.america.brazil import IBGE_REGISTER


class BrazilianHoliday:
    def __init__(self, name, date, state_ibge, city_ibge, coverage, leave_type):
        self.state_ibge = state_ibge
        self.city_ibge = city_ibge
        self.city_name = ""
        self.coverage = coverage
        self.leave_type = leave_type
        self.name = name
        self.date = date


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
            holiday_leave_type = "C"
        else:
            holiday_leave_type = "F"
        holiday_obj = BrazilianHoliday(
            holiday_name, holiday_date, None, None, "N", holiday_leave_type
        )
        if not any(x.name == holiday_obj.name for x in holidays_set):
            holidays_set.append(holiday_obj)

    # Get brazilian bank holidays
    cal = BrazilBankCalendar()
    for bank_holidays in cal.holidays(year):
        holiday_name = bank_holidays[1]
        holiday_date = bank_holidays[0]

        holiday_obj = BrazilianHoliday(holiday_name, holiday_date, None, None, "N", "B")
        if not any(x.name == holiday_obj.name for x in holidays_set):
            holidays_set.append(holiday_obj)

    # Get holidays from brazilian state
    for register in IBGE_REGISTER.items():
        state_ibge = re.sub("BR-IBGE-", "", register[0])
        if len(state_ibge) == 2:
            cal_state = IBGE_REGISTER[register[0]]()
            for state_holidays in cal_state.holidays(year):
                holiday_name = state_holidays[1]
                holiday_date = state_holidays[0]

                holiday_obj = BrazilianHoliday(
                    holiday_name, holiday_date, state_ibge, None, "E", "F"
                )

                # Check if is just a state holiday
                if not any(
                    (x.name == holiday_obj.name and not x.state_ibge)
                    for x in holidays_set
                ):
                    holidays_set.append(holiday_obj)

    # Get brazilian municipal holidays
    for register in IBGE_REGISTER.items():
        city_ibge = re.sub("BR-IBGE-", "", register[0])
        state_ibge = city_ibge[0:2]
        if len(city_ibge) > 2:
            cal_city = IBGE_REGISTER[register[0]]()

            for city_holiday in cal_city.holidays(year):
                holiday_name = city_holiday[1]
                holiday_date = city_holiday[0]

                holiday_obj = BrazilianHoliday(
                    holiday_name, holiday_date, state_ibge, city_ibge, "M", "F"
                )

                # Check if is just a municipal holiday
                if not any(
                    (x.name == holiday_obj.name and not x.city_ibge)
                    for x in holidays_set
                ):
                    holidays_set.append(holiday_obj)
    return holidays_set
