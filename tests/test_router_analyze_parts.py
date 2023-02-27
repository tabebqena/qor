import copy
import pytest

from qor.router import analyze_part, path_converters


def test_analyze_part():
    assert analyze_part("", path_converters) == ("", path_converters["string"])
    assert analyze_part("id", path_converters) == ("id", path_converters["string"])
    assert analyze_part("id:string", path_converters) == (
        "id",
        path_converters["string"],
    )
    assert analyze_part("id:int", path_converters) == ("id", path_converters["int"])
    assert analyze_part("id:float", path_converters) == ("id", path_converters["float"])
    assert analyze_part("id:float", path_converters) == ("id", path_converters["float"])


def test_analayze_part_long():
    with pytest.raises(Exception) as e:
        analyze_part("id:int:extra", path_converters)


def test_analyze_part_custom():
    converters = copy.copy(path_converters)
    converters["any"] = ".*"
    assert analyze_part("id:any", converters) == ("id", converters["any"])


def test_analyze_part_not_found():
    with pytest.raises(Exception) as e:
        analyze_part("id:any", path_converters)


def test_analyze_part_rejex():
    assert analyze_part("id:re:.*", path_converters) == ("id", ".*")
