Welcome to Qor
==============

*Qor* is a python web framework on top of `kore` server. 
**Kore** is a web application platform for writing scalable, concurrent web based processes in C or Python. 

**Qor** built to facilitate developing `kore` application.


Installation
------------

- First, you should install kore_ :

.. _kore: https://docs.kore.io/4.2.0/install.html


- check `kore` installation:
  
  
  ..  code-block:: bash

    $ kore -h


This command should print the help information about the `kore` server.


- install `Qor`:


.. admonition:: NB

    consider creating virtual enviroment first.


  ..  code-block:: sh 
    
    $ pip install git+https://github.com/tabebqena/qor.git



A Minimal Application
---------------------


.. attention:: The following bash commands assume that you are using lunux OS.


.. code-block:: sh

    # craete folder
    mkdir qor_app
    cd qor_app
    # create virtual env
    python3 -m venv .venv
    # activate venv
    .venv/bin/activate
    # instal qor
    pip install git+https://github.com/tabebqena/qor.git
    touch app.py

Now, Open the `app.py` file and write the following content in it:

.. code-block:: python

    from qor import Qor

    app = Qor()

    @app.route("/")
    def hello_world(request, *args, **kwargs):
        return "<p>Hello, World!</p>"
    
    # This line is a must
    koreapp =app
  

save the file and type ``qor run`` command in your terminal.


.. code-block:: text

    $ qor run
     

You should see many lines stating that the `kore` server is running at `http://127.0.0.1:8888`.

Now head over to http://127.0.0.1:8888/, and you should see the `hello
world` statement.


let's analyze it
----------------

.. code-block:: python

    app = Qor()

*  We create app instance. In this simple example, we pass no arguments, But
    in real applications, you mostly needs to pass some arguments.

.. code-block:: text

    @app.route("/")

*  This decorator is used to add route to the application. 
    The first argument is the path. The `/` path means that the function decorated by this decorator
    will be executed when the user make request (browser mostly) to the `/` in our domain.
    if your domain is `www.example.com`, the  `hello_world` method will be executed when the user type 
    `http://www.example.com/` in his browser.


.. code-block:: python

    def hello_world(request, *args, **kwargs):
        return "<p>Hello, World!</p>"


*  This is the heavy lifting part of our application, you can call it the `controller` or the `view` function. However, We will call it `handler`. 


   Whatever the name, This method is the building block of your application. You should create your functions by the same or equaivalent signature:
    - recieve the `request` object as first positional argument.
    - recieves many arguments `*args` ( we will talk about this shortly)
    - recieves many keywords `**kwargs` ( has no use now, but better to be ready for possible future implementation. by writing the function by this way, your legacy code willn't break in the future)
    - lastly, the function returns the result you want to display in the user browser. In our case it is just `return "<p>Hello, World!</p>"`.
    


And the last line:

    .. code-block:: python

      # This line is a must
      koreapp =app


* This line is very important. till this release, the `kore` server will search for this name `koreapp`. If you forget to specify your app with this name, The `kore` will shutdown silently or at least will not serve your application.



.. admonition:: can't find application::

    `Qor` tries to be smart, when you type `qor run` it search for the your application in the following order.
          
          
       1. first, from the command line, if you type:


          .. code-block:: sh
           
              $ qor run /path/to/my/app.py


       `qor` will use this path and will not try to search beyond it.

          
       1. then from the enviroment variable `KORE_APP`.
       2. then from file named `app.py` that presents in the current working dir.

       To debug, you will find a line like this:

       >> $ got app 'path/to/the/app.py'



.. warning:: development server

    you can run your app by `kore <PATH>` command. Internally, The `qor run` command is executing `kore <PATH>`. But there is 2 important differences:

    - this command is suitable for development and you shouldn't use it in production (use `kore <>` in production).
    - this command start a watcher for your files. If any `*.py` file change in your current directory or below it, the `kore` will be auto restarted for you.



.. admonition:: auto restarting

    This behavior is suitable for development and will give you a suitable enviroment. You can focus on your real work instead of being busy by remembring to restart the server after each minor changes. But you should know the internals of it. 
    For each restart, the `kore` server been killed then launched again again. If there is an error in killing the `kore` ( which may occur rarley), you should manually kill it.
    In short, killing `kore` is done by sending `SIGTERM` or `SIGQUIT` to its process.
    
    In linux, you can type:

      .. code-block:: sh
          
             $ kill KOR_PROCESS_ID
           

      >> How to know the pid?
      >>> It is writting the `kore.pid` file. or you can search fro it by :abbreviation:

      .. code-block:: sh
          
             $ pidof kore
      
          If the `kore` server still running, the next time you try to run `qor` you will got error states that the `kore` can't create server on the `127.0.0.1:8888` because the port is already in use..


Routing
-------

Modern web applications use meaningful URLs to help users. Users are more
likely to like a page and come back if the page uses a meaningful URL they can
remember and use to directly visit a page.

Use the `~qor.Qor.route` decorator to bind a function to a URL.



.. code-block:: python

      @app.route('/')
      def hello_world(request, *args, **kwargs):
          return '<p>Hello World</>'



Also, There is many alternatives like `~qor.Qor.get`, `~qor.Qor.post`, `~qor.Qor.put`, `~qor.Qor.patch` and `~qor.Qor.delete` decorators. they create routes specified for thier methods only. You can also specify the method as an argument to the `~qor.Qor.route` decorator:


.. code-block:: python


    @app.get('/hello', methods=["get"]) # get only route
    def hello(request, *args, **kwargs):
        return 'Hello, World'
    

    @app.route('/posts', methods=["get", "post"]) # get & post route
    def posts(request, *args, **kwargs):
        return 'posts'
    
    # Also, This is acceptable
    @app.route('/posts')
    @app.post('/posts')
    @app.route('/posts', methods=["delete"])        
    def posts(request, *args, **kwargs):
        return 'posts'
    


Dynamic Routing
```````````````


Most of times, you need to specify a variable part in your route. route like `/posts/<post_id>` is adynamic route, because you specify it with the variable `post_id` and `Qor` will translate this variable during routing.


.. code-block:: python

    @app.route('/user/<username>')
    def user_page(request,  *args, **kwargs):
        username = args[0]
        return f'User {username}'
    
    """The following is the same, Note that the `*args` was replaced by `username` as I know the name & the count of the recieved arguments """
    @app.route('/user/<username>')
    def user_page(request, username, **kwargs):
        return f'User {username}'
    

    @app.route('/post/<post_id:int>')
    def show_post(request, post_id, **kwargs):
        # show the post with the given id, the id is an integer
        return f'Post {str(post_id)}'



You can use the following converters inside the path decleration:

========== ==========================================
``string`` (default) accepts any text without a slash
``int``    accepts positive integers
``float``  accepts positive floating point values
``re``     accepts regex
========== ==========================================

The dynamic path part should be one of the following syntaxes:

======================================= ================================================================
``<variable_name>``                      The `<variable_name>` will be a string (default) 
``<variable_name:converter_name>``       The `<variable_name>` will be the same type of the converter 
``<variable_name:re:MY_REGEX_HERE>``     The `<variable_name>`
======================================= ================================================================


URL Reversing
`````````````

You know that the `/posts/<post_id:int>` is the dynamic path that will translate to `posts/1` or `posts/2` during routing. Now, you should ask: How to build url for specific post?

Ofcourse, you can do something like `post_path = '/posts/'+post_id`, but this is unmaintainable error prone code.
So, the idea of url reversing come to fill this niche. 

First, we should name the routes that we want to build url for it, Each route can optionally have a name, you pass it as argument to the decorator.

.. code-block:: python

    from qor import Qor

    app = Qor()

    @app.route("/", name="index_page")
    def index(request, *args, **kwargs):
      return "<p>Hello World</p>"
    
    @app.route("/posts", name="post_list")
    def posts(request, *args, **kwargs):
      return "Posts"
    
    @app.route("/posts/<post_id:int>", name="post_detail")
    def single_post(request, post_id, **kwargs):
      return f"Post {str(post_id)}"
    
    koreapp = app


Now `Qor` knows that you name the `index` handler as `index_page` and you intend to use this name in building url for this route. similiary, `Qor` knows that the `post_list` and `post_detail` are the names that should reverse to the `posts` & `single_post` handlers respectively. To build a URL to a specific handler, you can use the `~qor.Qor.reverse` method or its proxy `~qor.Request.reverse`. It accepts the name of the route as its first argument and any number of keyword arguments, each corresponding to a variable part of the route.
 

.. code-block:: python

    print(app.reverse("index_page"))  # will print "/"
    print(app.reverse("post_list"))  # will print "/posts"
    print(app.reverse("post_detail", post_id=1))  # will print "/posts/1"
    print(app.reverse("post_detail", post_id=88))  # will print "/posts/88"
    
    
This is a handy method for redirection and creating paths. Suppose that you have a handler that creates a new post based on the data the user send to you. It is meaningful to return the url for the new created post:
    

.. code-block:: python

    from qor import Qor

    koreapp = Qor()

    @koreapp.route("/posts", methods=["post"], name="post_detail")
    def create_post(request,  **kwargs):
      # craete post

      return {
         "status": "success",
         "message": "post created successfully",
         "url" : request.reverse("post_detail", post_id=the_post_id)      
      }



Rendering Templates
-------------------

.. warning:: 
    (This feature is not completed yet)

`Qor` has a provision feature for creating templates for you. To render a template you can use the `~qor.Request.render_template` method.  All you have to do is provide the name of the template and the
variables you want to pass to the template engine as keyword arguments.
Here's a simple example of how to render a template::


    from qor import Qor

    koreapp = Qor()

    @koreapp.route("/posts")
    def post_list(request,  **kwargs):
      # get posts from the DB
      return request.render_template("post_list.html", posts=posts)


`Qor` will search for the `post_list.html` template in the `templates` folder, next to your app (This behavior can be changed).

**Example**: a module::

    app.py
    /templates
        /post_list.html


For templates you can use the full power of Jinja2 templates.  Head over
to the official `Jinja2 Template Documentation
<https://jinja.palletsprojects.com/templates/>`_ for more information.

Here is an example template:

.. sourcecode:: html+jinja

    <!doctype html>
    <!-- post_list.html  -->
    <title>posts list</title>
    {% for post in posts %}

    <h3>{{post.title}}</h3>
    <a href="{{  request.reverse('post_detail', post_id=post.post_id)  }}">show</a>

    {% endfor %}
    

Inside templates you also have access to the:

`app`, `~qor.wrappers.Request`, `~qor.g` and `~qor.reverse` 
 


Accessing Request Data
----------------------

For web applications it's crucial to react to the data a client sends to
the server. In Qor this information is provided by the request object that your handler recieve as a first argument.
In general, It is a thin wrapper around the `kore.http_request` that `kore` pass on each request. head over `kore documentation <https://docs.kore.io/4.2.0/api/python.html#httpmodule>`_ for more information.

In the `Request` object you can access:

1. app : `Qor` application.
2. route: the route info if available (always available inside your handler).
3. g: an empty dictionary, that is specific for each reaquest & can be used for storing data across the request lifetime.
4. method: the request method `get`, `post` etc.
5. host
6. agent
7. path
8. body: entire encoming http body.
9. headers: dictionary of request headers.
10. content_type.
11. mime_type.
12. is_form property: `True` if the request has a form content type.
13. is_multipartproperty: `True` if the request has a multipart form content type.
14. is_json property: `True` if the request has a json content type.
15. json property: The entire request body as json, if the `is_json` is `True`.
16. form property: The entire request body, if the `is_form` is `True`.
17. cookie method: recieves the cookie name and returns its value or `None`.
18. argument: recieves the name of the argument & returns  the value if present. N.B:. argument may be path argument or request body argument & has a special method for decleration.
19. response_header method: recieves the header name & value as its arguments & it set the header for the upgoing response.
20. get_response_header method: recieves the header name &  return the response header value if set before.
21. redirect method: recieves the url as first argument & return a response redirect to it.
22. reverse: proxy for `qor.Qor.reverse`.
23. render_template: return a template response.


Cookies
```````

To access cookies you can use the `~qor.Request.cookie`
method. To set cookies you can use the  `~qor.Request.set_cookie`

Reading cookies::


    from qor import Qor

    koreapp = Qor()

    @koreapp.route('/')
    def index(request, *args, **kwargs):
        username = request.cookie('username')
        # ...

Storing cookies::

    from qor import Qor

    koreapp = Qor()

    @koreapp.route('/')
    def index(request, *args, **kwargs):
        resp = request.set_cookie('username', 'the username')
        return resp


Redirects
---------

To redirect a user to another route, use the `~qor.Request.redirect`:

.. code-block:: python

    from qor import Qor

    @app.route('/')
    def index(request, *args, **kwargs):
        return request.redirect(request.reverse('login'))


About Responses
---------------

The return value from a handler function is automatically converted into
a response object for you. The status and the content type are assumed from the response.

`Qor` expect to recieve a tuple of 2-objects or one object.

1. If you return a tuple, The first item of it should be the integer status code. The second object will be used as the response body.
2. If you return an object, The status code assumed to be 200, and the object will be used as a response body.

The returned object determines the content type:
1. `str`, `bytes`, `int`, `float`: the content type will be `text/html`.
2. `list`, `dict`: the content type will be `application/json`

This behavior is accomplished by the `qor.Qor.return_value_parser` object, which you can override or provide your own.

APIs with JSON
``````````````

A common response format when writing an API is JSON. It's easy to get
started writing such an API with `Qor`. If you return a ``dict`` or
``list`` from a handler, it will be converted to a JSON response.

.. code-block:: python

    @app.route("/me")
    def me_api(request, *args, **kwargs):
        user = get_current_user()
        return {
            "username": user.username,
            "theme": user.theme,
            "image": request.reverse("user_image", filename=user.image),
        }

    @app.route("/users")
    def users_api(request, *args, **kwargs):
        users = get_all_users()
        return [user.to_json() for user in users]


For complex types such as database models, you'll want to use a
serialization library to convert the data to valid JSON types first.
There are many serialization libraries that support more complex applications like `marchmallow`.


Sessions
--------

``TODO``


Message Flashing
----------------

``TODO``


Logging
-------

Sometimes you might be in a situation where you deal with data that
should be correct, but actually is not.  For example you may have
some client-side code that sends an HTTP request to the server
but it's obviously malformed.  This might be caused by a user tampering
with the data, or the client code failing.  Most of the time it's okay
to reply with ``400 Bad Request`` in that situation, but sometimes
that won't do and the code has to continue working.

You may still want to log that something fishy happened. This is where
logging come in handy. `kore` C framework has a `log` function taht you can access from your handlers.

Here are some example log calls::


    app.log(' message to be logged ', app.LOG_INFO)
    request.log(' message to be logged ', app.LOG_INFO)
    request.log_info(' info to be logged ')
    request.log_debug(' debug data to be logged ')
    request.log_error(' error data to be logged ')
    request.log_exception(exception)
    
In development, The log messages will be displayed on the terminal. for development, You should set the `logfile` config and pass it to `Qor`


    from qor import Qor

    config = { "logfile": "log"}

    koreapp = Qor(config=config)

    # all logs will be added to the `log` file