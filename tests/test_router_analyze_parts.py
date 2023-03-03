import copy
import pytest

from qor.router import analyze_part, path_converters


def test_analyze_part_empty():
    part = ""
    part_name = ""
    rv = analyze_part(part, path_converters)
    name = rv[0]
    regex = rv[1]
    to_python = rv[2]

    assert name == part_name
    assert regex == path_converters["string"][0]
    assert isinstance(to_python(""), str)


def test_analyze_part_noregex():
    part = "id"
    part_name = "id"
    rv = analyze_part(part, path_converters)
    name = rv[0]
    regex = rv[1]
    to_python = rv[2]

    assert name == part_name
    assert regex == path_converters["string"][0]
    assert isinstance(to_python(""), str)


def test_analyze_part_string():
    part = "id:string"
    part_name = "id"
    rv = analyze_part(part, path_converters)
    name = rv[0]
    regex = rv[1]
    to_python = rv[2]

    assert name == part_name
    assert regex == path_converters["string"][0]
    assert isinstance(to_python(""), str)


def test_analyze_part_int():
    part = "id:int"
    part_name = "id"
    rv = analyze_part(part, path_converters)
    name = rv[0]
    regex = rv[1]
    to_python = rv[2]

    assert name == part_name
    assert regex == path_converters["int"][0]
    assert isinstance(to_python("1"), int)


def test_analyze_part_float():
    part = "id:float"
    part_name = "id"
    rv = analyze_part(part, path_converters)
    name = rv[0]
    regex = rv[1]
    to_python = rv[2]

    assert name == part_name
    assert regex == path_converters["float"][0]
    assert isinstance(to_python("1"), float)


def test_analayze_part_long():
    with pytest.raises(Exception) as e:
        analyze_part("id:int:extra", path_converters)


def test_analyze_part_custom():
    part = "id:any"
    regex = ".*"
    converters = copy.copy(path_converters)
    converters["any"] = (regex, lambda v: v)

    part_name = "id"
    rv = analyze_part(part, converters)
    assert rv[0] == part_name
    assert rv[1] == regex
    assert rv[2](5) == 5


def test_analyze_part_not_found():
    with pytest.raises(Exception) as e:
        analyze_part("id:any", path_converters)


def test_analyze_part_regex():
    part = "id:re:.*"
    regex = ".*"
    part_name = "id"
    rv = analyze_part(part, path_converters)
    assert rv[0] == part_name
    assert rv[1] == regex
    assert rv[2](5) == 5
