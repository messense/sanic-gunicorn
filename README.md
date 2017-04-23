# sanic-gunicorn

[Gunicorn](http://gunicorn.org/) worker for [Sanic](https://github.com/channelcat/sanic)

**Notice**: For Sanic v0.5.0 and above, please use [its built-in Gunicorn support](http://sanic.readthedocs.io/en/latest/sanic/deploying.html#running-via-gunicorn).

## Installation

```bash
$ pip install -U sanic-gunicorn
```

## Usage

```bash
$ gunicorn --bind localhost:8000 --worker-class sanic_gunicorn.Worker your_app_module:app
```
