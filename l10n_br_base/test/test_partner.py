from functools import partial
import pytest


def test_validate_ie_param():
    from ..partner import validate_ie_param
    assert validate_ie_param('rs', '096/0328009')
    assert not validate_ie_param('rs', '096/0000009')


def test_validate_ie_sp():
    from ..partner import res_partner
    validate_ie_sp = partial(res_partner._validate_ie_sp.im_func, None)
    assert validate_ie_sp('674008473116')
    assert not validate_ie_sp('074008473116')


@pytest.mark.xfail
def test_validate_ie_param_mt():
    from ..partner import validate_ie_param
    assert validate_ie_param('mt', '130693774')
