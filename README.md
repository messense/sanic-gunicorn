# sanic-gunicorn

[Gunicorn](http://gunicorn.org/) worker for [Sanic](https://github.com/channelcat/sanic)

## Installation

```bash
$ pip install -U sanic-gunicorn
```

## Usage

```bash
$ gunicorn --bind localhost:8000 --worker-class sanic_gunicorn.Worker your_app_module:app
```
