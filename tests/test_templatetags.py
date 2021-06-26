import pytest

from adminactions.templatetags.massupdate import (fields_values,
                                                  link_fields_values,)


@pytest.mark.parametrize("data", [{'field1': [(1, 'value1.1')]},
                                  {'field1': ['value1.1']},
                                  {'field1': [22]},
                                  ],
                         ids=("list", "str", "int"))
def test_link_fields_values(data):
    assert link_fields_values(data, "field1")


def test_fields_values():
    data = {'name1': ['value1.1', 'value1.2'], 'name2': ['value2.1', 'value2.2'], }
    assert fields_values(data, 'name1') == "value1.1,value1.2"
