![alt text](screenshot_dark.png)

# An Otter Wiki

An Otter Wiki is Python-based software for collaborative content
management, called a [wiki](https://en.wikipedia.org/wiki/Wiki). The
content is stored in a git repository, which keeps track of all changes.
[Markdown](https://daringfireball.net/projects/markdown) is used as
Markup language. An Otter Wiki is written in [python](https://www.python.org/)
using the microframework [Flask](http://flask.pocoo.org/).
[halfmoon](https://www.gethalfmoon.com) is used as CSS framework and [CodeMirror](https://codemirror.net/) as editor.
[Font Awesome Free](https://fontawesome.com/license/free) serves the icons.

### Notable Features

- Minimalistic interface (with dark-mode)
- Full changelog and page history
- User authentication
- Page Attachments
- A very cute Otter as logo (drawn by [Christy Presler](http://christypresler.com/) CC BY 3.0).

## Quick and dirty standalone demo

1. Install the prerequisites
    1. Debian / Ubuntu
    ```bash
    apt install git build-essential python3-dev python3-venv
    ```
    2. RHEL8 / Fedora / Centos8 / Rocky Linux 8
    ```bash
    yum install make python3-devel
    ```
2. Clone the otterwiki repository and enter the directory
```bash
git clone https://github.com/redimp/otterwiki.git
cd otterwiki
```
3. Create and initialize the repository where the otterwiki data lives
```bash
mkdir -p app-data/repository
# initialize the empty repository
git init app-data/repository
```
4. Create a minimal configuration file
```bash
echo "REPOSITORY='${PWD}/app-data/repository'" >> settings.cfg
echo "SQLALCHEMY_DATABASE_URI='sqlite:///${PWD}/app-data/db.sqlite'" >> settings.cfg
echo "SECRET_KEY='$(echo $RANDOM | md5sum | head -c 16)'" >> settings.cfg 
```
5. Run make to setup a virtual environment and run a local server on port 8080.
```
make
```
6. Open the wiki in your browser <http://127.0.0.1:8080>. You can create and edit pages as anonymous user without any further configuration. Please note: This setup is not for production use!

## Deployment

An Otter Wiki can be deployed via docker/podman or as WSGI application. The deployment via `docker-compose` is recommended.
To enable user registration a mail account has to be configured, see Configuration.

## Deployment from source via docker-compose

1. Clone the repository
```bash
git clone https://github.com/redimp/otterwiki.git
cd otterwiki
```
2. Create and adjust the file docker-compose.override.yml
```bash
cp docker-compose.override.yml.skeleton docker-compose.override.yml
``` 
The use of `docker-compose.override.yml` is recommended, since the `docker-compose.yml` may change when updating the repository.
3. Start the container
```bash
docker-compose up -d
```
4. Access the wiki via <http://127.0.0.1:8080/>.

### Deployment as WSGI application

<mark>TODO</mark>

- [WSGI container](https://flask.palletsprojects.com/en/2.0.x/deploying/wsgi-standalone/)

## Configuration

Create a `settings.cfg` based upon `settings.cfg.skeleton` and set the
variables fitting to your environment.

**The basic configuration must be done in the `settings.cfg`** (The
Docker container does this for you.) All other configurations can be
configured in the _Settings_ as admin user.

### Basic Configuration

| Variable         |  Example        | Description                                  |
|------------------|-----------------|----------------------------------------------|
| `SECRET_KEY`     | `'CHANGE ME'`   | Choose a random string that is used to encrypt user session data |
| `REPOSITORY`     | `'/path/to/the/repository/root'` | The absolute path to the repository storing the wiki pages |
| `SQLALCHEMY_DATABASE_URI` | `'sqlite:////path/to/the/sqlite/file'` | The absolute path to the database storing the user credentials |

For the `SQLALCHEMY_DATABASE_URI` see <https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/#connection-uri-format>.

### Branding

| Variable         |  Example        | Description                                  |
|------------------|-----------------|----------------------------------------------|
| `SITE_NAME`      | `'Otterwiki'`   | The `SITE_NAME` displayed on every page and email |
| `SITE_LOGO`      | `'/Home/a/logo.png'` | Customize navbar logo url (can be a page attachment) |

### Permission configuration

| Variable         |  Example        | Description                                  |
|------------------|-----------------|----------------------------------------------|
| `READ_ACCESS`    | `'ANONYMOUS'`   | Read access to wiki pages and attachments    |
| `WRITE_ACCESS`   | `'REGISTERED'`  | Write access to wiki pages                   |
| `ATTACHMENT_ACCESS` | `'APPROVED'` | Write acccess to attachments                 |
| `AUTO_APPROVAL`  | `False`         | With `AUTO_APPROVAL=True` users are approved on registration |
| `EMAIL_NEEDS_CONFIRMATION`  | `True`         | With `EMAIL_NEEDS_CONFIRMATION=True` users have to confirm their email address |
| `NOTIFY_ADMINS_ON_REGISTER` | `True`  | Notify admins if a new user is registered |

There are four types of users in the Otterwiki: `ANONYMOUS` are non logged in users.
Users that registered via email and are logged in are `REGISTERED`, users approved via
the settings menu by an admin are `APPROVED`. In addition to the `APPROVED` flag the `ADMIN`
flag can be set. Users with the `ADMIN` flag can edit (and approve) other users. The first registered user is flagged as admin.

### Mail configuration

An Otter Wiki is using [Flask-Mail](https://pythonhosted.org/Flask-Mail/). 

| Variable         |  Example        | Description                                  |
|------------------|-----------------|----------------------------------------------|
| `MAIL_DEFAULT_SENDER` | `'otterwiki@example.com'` | The sender address of all mails |
| `MAIL_SERVER`    | `'smtp.googlemail.com'` | The smtp server address              |
| `MAIL_PORT`      | `465`           | The smtp server port                         |
| `MAIL_USERNAME`  | `'USERNAME'`    | Username for the mail account                |
| `MAIL_PASSWORD`  | `'PASSWORD'`    | Password for the mail account                |
| `MAIL_USE_TLS`   | `False`         | Use TLS encrytion                            |
| `MAIL_USE_SSL`   | `True`          | Use SSL encryption                           |


## Developers Guide

### Setup

1. Clone the repository
2. Install Dependencies `make venv`
3. Run tests and coverage `make coverage`

### Running the server

If using Make:
   - `make debug`
   
If using IDE:
   - Setup enviornment variable:
     - FLASK_DEBUG=True
     - FLASK_APP=otterwiki.server
     - OTTERWIKI_SETTINGS=../settings.cfg
   - Run `server.py`

[modeline]: # ( vim: set fenc=utf-8 spell spl=en sts=4 et tw=72: )
