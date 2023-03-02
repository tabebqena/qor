from qor.router import Router


def test_build_routes_nesting():
    main_router = Router()
    main_router.add_route("/", None, "main")

    router1 = Router(name="first")
    router2 = Router(name="second")
    router1.add_route("/first_index", name="first_index", handler=None)
    router1.add_route("first_blog", name="first_blog", handler=None)
    router1.add_route("first_about/", name="first_about", handler=None)
    router1.add_route("/first_contact/", name="first_contact", handler=None)
    router1.add_route("//first_privacy/", name="first_privacy", handler=None)

    router2.add_route("/second_index", name="second_index", handler=None)
    router2.add_route("second_blog", name="second_blog", handler=None)
    router2.add_route("/second_about/", name="second_about", handler=None)
    router2.add_route("/second_contact/", name="second_contact", handler=None)
    router2.add_route("//second_privacy/", name="second_privacy", handler=None)

    main_router.mount_router("first", router1)
    router1.mount_router("second", router2)
    main_router.build_routes()

    main = main_router.find_route_by_name("main")
    assert main
    assert main.name == "main"
    assert main.raw_path == "/"

    first_index = main_router.find_route_by_name("first:first_index")
    assert first_index
    assert first_index.name == "first:first_index"
    assert first_index.raw_path == "/first/first_index"

    first_blog = main_router.find_route_by_name("first:first_blog")
    assert first_blog
    assert first_blog.name == "first:first_blog"
    assert first_blog.raw_path == "/first/first_blog"

    first_about = main_router.find_route_by_name("first:first_about")
    assert first_about
    assert first_about.name == "first:first_about"
    assert (
        first_about.raw_path == "/first/first_about/"
    )  # because the input url has trailing slash

    first_contact = main_router.find_route_by_name("first:first_contact")
    assert first_contact
    assert first_contact.name == "first:first_contact"
    assert first_contact.raw_path == "/first/first_contact/"

    first_privacy = main_router.find_route_by_name("first:first_privacy")
    assert first_privacy
    assert first_privacy.name == "first:first_privacy"
    assert (
        first_privacy.raw_path == "/first//first_privacy/"
    )  # because tha input has double slashes

    second_index = main_router.find_route_by_name("first:second:second_index")
    assert second_index
    assert second_index.name == "first:second:second_index"
    assert second_index.raw_path == "/first/second/second_index"

    second_blog = main_router.find_route_by_name("first:second:second_blog")
    assert second_blog
    assert second_blog.name == "first:second:second_blog"
    assert second_blog.raw_path == "/first/second/second_blog"

    second_about = main_router.find_route_by_name("first:second:second_about")
    assert second_about
    assert second_about.name == "first:second:second_about"
    assert second_about.raw_path == "/first/second/second_about/"

    second_contact = main_router.find_route_by_name(
        "first:second:second_contact"
    )
    assert second_contact
    assert second_contact.name == "first:second:second_contact"
    assert second_contact.raw_path == "/first/second/second_contact/"

    second_privacy = main_router.find_route_by_name(
        "first:second:second_privacy"
    )
    assert second_privacy
    assert second_privacy.name == "first:second:second_privacy"
    assert (
        second_privacy.raw_path == "/first/second//second_privacy/"
    )  # because tha input has double slashes
