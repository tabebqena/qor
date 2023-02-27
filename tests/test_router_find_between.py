from qor.router import END, START, find_between


def test_find_between():
    assert find_between("<string>", START, END) == "string"
    assert find_between("<string", START, END) == ""
    assert find_between("string>", START, END) == ""
    assert find_between("string", START, END) == ""
    assert find_between("string><", START, END) == ""
    assert find_between("string<>", START, END) == ""
    assert find_between("><string", START, END) == ""
    assert find_between("<>string", START, END) == ""


#
