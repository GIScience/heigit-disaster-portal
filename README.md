# HeiGIT Disaster Portal API

> Copyright Notice: This repository is licensed under the GNU AGPLv3 license. The basic structure is generated using
> the [FastAPI project generator](https://github.com/tiangolo/full-stack-fastapi-postgresql) (MIT license).
> If you want to do a similar project, you might want to start there.

The HeiGIT disaster portal API was developed to allow the accessing, adding, deleting and editing of features that
can be used in requests to HeiGIT services in the form of a portal system between applications or users and
services provided by HeiGIT.
This portal should act as a single entry place to the various services ([openrouteservice], [ohsome] etc.) as well as
allowing additional processing to be performed on either the requests made to these services, or the responses
returned from them.

[openrouteservice]: https://openrouteservice.org "ORS website"
[ohsome]: https://ohsome.org "ohsome website"

In the initial version, the portal will only communicate with [openrouteservice], and will be used for adding avoid
areas to requests which will be provided by an external source.

To accomplish this, there will need to be two APIs - one for maintaining the database of features, and one for making
requests against the HeiGIT services.

The API for communicating with services should be kept as close to the original requests as possible with minimal
alterations and additional parameters.

The avoid-areas functionality should be able to identify features from the database that would be avoid-areas for the
request without the user having to explicitly pass these areas in with their request.
It should also be able to strip these derived areas from the meta information in the response, where normally the full
query passed to openrouteservice is added.
In the case of the portal, the request to [openrouteservice] will contain information not directly specified by the user,
and it may be desired (e.g. to reduce network transmission) to remove this information from the response.

Requirements:
- docker
- docker-compose (included in mac and windows docker installations)


## Production setup

```sh
# copy .env-sample to .env and adjust settings
cp .env-sample .env

# builds the docker disaster-area-portal image and dap-api container
docker-compose build

# deploy dap-api and dap-db in background
docker-compose up -d

# check api logs
docker logs -f dap-api
docker logs --tail 200 dap-api

# grep docker logs using `2>&1`
docker logs dap-api 2>&1 | grep WARNING
```

The interactive api documentation can be accessed at http://localhost:8080/api/v1/docs
or alternative documentation on http://localhost:8080/api/v1/redoc

## Development setup

Requirements:
- docker
- docker-compose (included in mac and windows docker installations)
- python3.10+

```
# Install poetry
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -

# enable poetry command (check [poetry documentation](https://python-poetry.org/docs/#enable-tab-completion-for-bash-fish-or-zsh) for shell completion setup)
source $HOME/.poetry/env
```

On some systems where python2 and python3 are installed in parallel (e.g. Ubuntu), above installation method for poetry 
may lead to problems due to poetry trying to use python 2. In case you see such an error message, try installing poetry 
via pip:
```
# Install poetry
pip3 install poetry
```

Now we can install all dependencies locally.
```
# install dependencies
poetry install --no-root
```

When using [PyCharm](https://www.jetbrains.com/pycharm/) you can use the [Poetry plugin](https://plugins.jetbrains.com/plugin/14307-poetry) 
to create an  interpreter with a python3.10 base or higher. It should use the virtual environment poetry has created. 
After creating it, you might need to close and open PyCharm again, so the Project uses now the correct interpreter and 
env. In case pycharm creates a separate virtual env, you could prevent poetry from creating further virtual envs by 
running:
```
poetry config virtualenvs.create false
```

Copy `.env-sample` to `.env` and adjust settings
```
cp .env-sample .env
```

Build the development image
```
docker-compose -f docker-compose.reload.yml build
```

This will build an image for 3 containers:
- dap-api-reload: fast api app with reload on file change (localhost:8081)
- dap-db: default postgis database also used with docker-compose.yml
- dap-test-db: separate test database to not clutter production db

Additionally, you can create a _docker-compose run configuration_ with PyCharm.
The advantage of this:
- only a few clicks to start
- automatically connects and opens the Services Toolbar (inspect docker stuff: images, containers, logs, bindings etc.)

1. Click the dropdown left of the Run Button (Play symbol) and click edit configurations
1. Click `+`(add new configuration) and choose Docker Compose
1. Set the name e.g. Reload
1. Compose file(s): `./docker-compose.reload.yml;`
1. Service(s): `dap-api-reload, dap-db, dap-test-db`
1. Click OK

Create and run development containers (or run the configuration)
```
docker-compose -f docker-compose.reload.yml up -d
```

_Note: The first time it will take some time until the db containers are configured. The dap-api-reload container won't
be able to connect right away._ 

You can test the service through the interactive docs on http://localhost:8081/docs

### Debugging

To be able to add breakpoints you need to add a _python run configuration_ for the [debug.py script](./dap_api/app/debug.py):
1. Click the dropdown left of the Run Button (Play symbol) and click edit configurations
1. Click `+`(add new configuration) and choose Python
1. Set the name e.g. Debug
1. Choose the file: `<project root>/dap_api/app/debug.py`
1. Interpreter should be the Project interpreter
1. The working directory should be `<project root>/dap_api/app`
1. Switch to the **EnvFile** tab (requires [EnvFile plugin](https://plugins.jetbrains.com/plugin/7861-envfile))
1. Click **Enable EnvFile**
1. Click the "+" to add both `.env` & `.env-dev` files located in the project root (in this order !). If the `.env` & `.env-dev` files do not show up, enable showing hidden files. (Mac: Command+Shift+Dot)   
1. Click OK


Click the debug button on the previously created run configuration.

To test if the breakpoints are working, add one in the return line of the root path function (`@app.get("/")` decorator)
and open http://localhost:8083 in your browser.


### Testing

**Make sure the `dap-test-db` container is running**
(If you always forget to do so, you can create a python run config for the `prestart_test_db.py` and let it run before the tests.)

To quickly run tests you can create a _pytest run configuration_:

1. Click the dropdown left of the Run Button (Play symbol) and click edit configurations
1. Click `+`(add new configuration) and choose pytest
1. Set the name e.g. Test
1. Interpreter should be the poetry one by default
1. Working directory: `<project_root>/dap_api/app/app/test`
1. Switch to the **EnvFile** tab (requires [EnvFile plugin](https://plugins.jetbrains.com/plugin/7861-envfile))
1. Click **Enable EnvFile**
1. Click the "+" to add both `.env` & `.env-dev` files located in the project root (in this order !)
1. Click OK
1. In the project browser, right-click on the folder `<project_root>/dap_api/app` and select Mark Directory as ->
Sources Root. (**NOT the `db_api/app/app` folder**)

Will open a user-friendly test interface, instead of scrolling through console :+1:
(Also having the option to only rerun failed tests)

You will also be able to debug the tests if you run this config in _debug mode_.

Alternatively you could run the tests within the `dap-api-reload` docker container:
```
# access the reload container
docker exec -i -t dap-api-reload bash

# run the tests (you should be in /app already)
pytest
```

### Coverage
For displaying test coverage during development there are 2 viable options:

1. Use the _Run pytest with coverage_ button (next to the debug button) for the previous pytest configuration.
This is a bit slower and creates coverage for the whole project.
Also, it is only available in the professional PyCharm Edition.
It will visually highlight all parts in the code that are not covered by tests yet.
 
1. Add `--cov=app --cov-report=term-missing` as _Additional Arguments_ to the pytest configuration.
With this the pytest output will also create a coverage report including the lines "missed", blocks that were not
executed with the test.
**important:** PyCharm somehow uses the same helpers for coverage & debugging, so when using this approach,
your breakpoints will not be hit. You can either add the coverage as a second pytest config, or add `--no-cov` as
_Additional Arguments_ to the pytest configuration, and switch back and forth between debug and coverage mode by
adding and removing `--no-cov` from the config.

> For the second option you need to check `Pytest: don't add "--no-header --no-summary -q"` in `Preferences` >
> `Advanced Settings` in PyCharm

Of course, you can also run pytest with coverage in the reload-container with
`pytest --cov=app --cov-report=term-missing`.

---

A html coverage report can be created to access coverage on an interactive website.
```
# run the tests with coverage (or add `--cov-report=html` to _Additional Arguments_)
pytest --cov=app --cov-report=html
```
Open the created `dap-api/app/app/tests/htmlcov/index.html` in any browser.

If this is working correctly the code coverage can be displayed e.g. with codecov as a badge on the repository.

### Database migrations

As during local development your app directory is mounted as a volume inside the container,
you can also run the migrations with `alembic` commands inside the container, and the migration
code will be in your app directory (instead of being only inside the container).
So you can add it to your git repository.

Make sure you create a "revision" of your models and that you "upgrade" your database with that revision every time you 
change them.
This is what will update the tables in your database.
Otherwise, your application will have errors.

* Start an interactive session in the backend container:

```console
$ docker exec -it dap-api-reload bash
```

* If you created a new model in `./app/app/models/`, make sure to import it in `./app/app/db/import_models.py`,
that imports all the models that will be used by Alembic.

* After changing a model (for example, adding a column) inside the container, create a revision, e.g.:

```console
$ alembic revision --autogenerate -m "Add column last_name to User model"
```

* Commit to the git repository the files generated in the alembic directory.

* After creating the revision, run the migration in the database (this is what will actually change the database):

```console
$ alembic upgrade head
```

If you don't want to start with the default models and want to remove them / modify them, from the beginning,
without having any previous revision, you can remove the revision files (`.py` Python files) under `./backend/app/alembic/versions/`.
Then create a first migration as described above.

See Readme in alembic for further information.
