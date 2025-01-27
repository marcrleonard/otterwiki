#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import os
import re
import otterwiki
import otterwiki.gitstorage
from flask import url_for
from datetime import datetime


def test_create_app_with_user(app_with_user):
    test_client = app_with_user.test_client()
    result = test_client.get("/")
    assert "<!DOCTYPE html>" in result.data.decode()
    assert "<title>" in result.data.decode()
    assert "</html>" in result.data.decode()


def test_db(app_with_user):
    from otterwiki.auth import SimpleAuth, check_password_hash, db

    # check that table 'user' exists
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    assert "user" in [str(x) for x in inspector.get_table_names()]

    # query all user
    all_user = SimpleAuth.User.query.all()
    assert len(all_user) == 1

    # query created user
    user = SimpleAuth.User.query.filter_by(email="mail@example.org").first()
    assert user.email == "mail@example.org"
    assert user.name == "Test User"
    # check hash
    assert True is check_password_hash(user.password_hash, "password1234")


def test_generate_and_check_hash(create_app):
    from otterwiki.auth import generate_password_hash, check_password_hash

    for password in ["abc123.!äüöß", "aedaiPaesh8ie5Iu", "┳━┳ ヽ(ಠل͜ಠ)ﾉ"]:
        for method in ["sha256", "sha512"]:
            hash = generate_password_hash(password, method=method)
            assert True is check_password_hash(hash, password)


def test_minimal_auth(app_with_user):
    # check auth defaults
    assert app_with_user.config.get("AUTH_METHOD") == ""


def login(client):
    return client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "password1234",
        },
        follow_redirects=True,
    )


def test_login(app_with_user, test_client):
    result = login(test_client)
    html = result.data.decode()
    assert "You logged in successfully." in html


def test_login_fail_without_app(test_client):
    html = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Invalid email address or password." in html


def test_login_fail_wrong_username(app_with_user, test_client):
    html = test_client.post(
        "/-/login",
        data={
            "email": "x@x.x",
            "password": "",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Invalid email address or password." in html


def test_login_fail_wrong_password(app_with_user, test_client):
    html = test_client.post(
        "/-/login",
        data={
            "email": "mail@example.org",
            "password": "xxx",
        },
        follow_redirects=True,
    ).data.decode()
    assert "Invalid email address or password." in html


def test_logout(test_client):
    result = login(test_client)
    html = test_client.get(
        "/-/logout",
        follow_redirects=True,
    ).data.decode()
    assert "You logged out successfully." in html


def test_login_required(test_client):
    html = test_client.get(
        "/-/settings",
        follow_redirects=True,
    ).data.decode()
    assert "Change Password" not in html
    assert "Please log in to access this page." in html


def test_settins_minimal(app_with_user, test_client):
    result = login(test_client)
    html = test_client.get(
        "/-/settings",
        follow_redirects=True,
    ).data.decode()
    assert "Change Password" in html


#
# test permissions
#
@pytest.fixture
def app_with_permissions(app_with_user, test_client):
    app_with_user.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_user.config["WRITE_ACCESS"] = "ANONYMOUS"
    # create a Home
    html = test_client.post(
        "/Home/save",
        data={
            "content_update": "There is no place like Home.",
            "commit": "Home: initial test commit.",
        },
        follow_redirects=True,
    ).data.decode()
    html = test_client.get("/Home").data.decode()
    assert "There is no place like Home." in html
    # update permissions
    app_with_user.config["READ_ACCESS"] = "REGISTERED"
    # and fetch again
    html = test_client.get("/Home").data.decode()
    assert "There is no place like Home." not in html

    with app_with_user.test_request_context() as ctx:
        yield app_with_user


def test_page_view_permissions(app_with_permissions, test_client):
    fun = "view"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert "There is no place like Home." in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun, path="Home"), follow_redirects=True)
    assert "There is no place like Home." not in rv.data.decode()
    # check for the toast
    assert "lack the permissions to access" in rv.data.decode()
    # check for the login form
    assert url_for("login") in rv.data.decode()
    assert 'name="password"' in rv.data.decode()
    assert rv.status_code == 200
    login(test_client)
    rv = test_client.get(url_for(fun, path="Home"))
    assert "There is no place like Home." in rv.data.decode()
    assert rv.status_code == 200


def test_page_blame_permissions(app_with_permissions, test_client):
    fun = "blame"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "There is no place like Home." in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 403
    assert "There is no place like Home." not in rv.data.decode()
    login(test_client)
    rv = test_client.get(url_for(fun, path="Home"))
    assert "There is no place like Home." in rv.data.decode()


def test_page_history_permissions(app_with_permissions, test_client):
    fun = "history"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "initial test commit" in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 403
    assert "initial test commit" not in rv.data.decode()
    login(test_client)
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "initial test commit" in rv.data.decode()


def test_page_index_permissions(app_with_permissions, test_client):
    fun = "pageindex"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun))
    assert rv.status_code == 200
    assert "Page Index" in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun))
    assert rv.status_code == 403
    assert "Page Index" not in rv.data.decode()
    login(test_client)
    rv = test_client.get(url_for(fun))
    assert rv.status_code == 200
    assert "Page Index" in rv.data.decode()


def test_page_changelog_permissions(app_with_permissions, test_client):
    fun = "changelog"
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "initial test commit" in rv.data.decode()
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 403
    assert "initial test commit" not in rv.data.decode()
    login(test_client)
    rv = test_client.get(url_for(fun, path="Home"))
    assert rv.status_code == 200
    assert "initial test commit" in rv.data.decode()


def test_page_edit_permissions(app_with_permissions, test_client):
    # update permissions
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"
    # helper
    pagename = "RandomEdit"
    # try to edit anonymous
    rv = test_client.get(url_for("edit", path=pagename))
    assert rv.status_code == 200
    html = rv.data.decode()
    # check that there is an editor in the html
    assert 'action="/{}/preview"'.format(pagename) in html
    assert "<textarea" in html
    # update permissions
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    app_with_permissions.config["WRITE_ACCESS"] = "REGISTERED"
    # try edit
    rv = test_client.get(url_for("edit", path=pagename))
    html = rv.data.decode()
    # check that there is an editor in the html
    assert rv.status_code == 403
    assert 'action="/{}/preview"'.format(pagename) not in html
    assert "<textarea" not in html
    # login
    login(test_client)
    # try edit
    rv = test_client.get(url_for("edit", path=pagename))
    html = rv.data.decode()
    assert rv.status_code == 200
    assert 'action="/{}/preview"'.format(pagename) in html
    assert "<textarea" in html


def test_page_save_permissions(app_with_permissions, test_client):
    # update permissions
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"
    # helper
    pagename = "RandomSaveTest"
    content = "Random Content"
    # try to edit anonymous
    rv = test_client.post(
        url_for("save", path=pagename),
        data={
            "content_update": content,
            "commit": "Home: initial test commit.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert content in rv.data.decode()
    # change permissions
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    app_with_permissions.config["WRITE_ACCESS"] = "REGISTERED"
    # try to edit anonymous (and fail)
    rv = test_client.post(
        url_for("save", path=pagename),
        data={
            "content_update": content,
            "commit": "Home: initial test commit.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 403
    # try to create (and fail)
    rv = test_client.post("/-/create", data={"pagename": "example"})
    assert rv.status_code == 403


def test_page_revert_permissions(app_with_permissions, test_client):
    # update permissions
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"
    # helper
    pagename = "Random Revert Test 0"
    old_content = "Random Content 0"
    # try to edit anonymous
    rv = test_client.post(
        url_for("save", path=pagename),
        data={
            "content_update": old_content,
            "commit": "initial test commit.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert old_content in rv.data.decode()
    # test view
    html = test_client.get("/{}/view".format(pagename)).data.decode()
    assert old_content in html
    # update content
    content = "Random Content 1"
    rv = test_client.post(
        url_for("save", path=pagename),
        data={
            "content_update": content,
            "commit": "updated content.",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert content in rv.data.decode()

    # find revision
    rv = test_client.get("/{}/history".format(pagename))
    html = rv.data.decode()
    revisions = re.findall(r"class=\"btn revision-small\">([A-z0-9]+)</a>", html)
    assert len(revisions) == 2
    latest_revision = revisions[0]

    # change permissions
    app_with_permissions.config["READ_ACCESS"] = "REGISTERED"
    app_with_permissions.config["WRITE_ACCESS"] = "REGISTERED"

    # try to revert non existing commit
    rv = test_client.get("/-/revert/{}".format(0000000))
    assert rv.status_code == 403

    # try revert form
    rv = test_client.get("/-/revert/{}".format(latest_revision))
    assert rv.status_code == 403
    # try to revert latest commit
    rv = test_client.post("/-/revert/{}".format(latest_revision))
    assert rv.status_code == 403

    # change permissions again
    app_with_permissions.config["READ_ACCESS"] = "ANONYMOUS"
    app_with_permissions.config["WRITE_ACCESS"] = "ANONYMOUS"

    # check revert form
    rv = test_client.get("/-/revert/{}".format(latest_revision))
    html = rv.data.decode()
    assert rv.status_code == 200
    assert "Revert commit [{}]".format(latest_revision) in html

    # try to revert latest commit
    rv = test_client.post("/-/revert/{}".format(latest_revision), follow_redirects=True)
    assert rv.status_code == 200

    # check if content changed
    html = test_client.get("/{}/view".format(pagename)).data.decode()
    assert old_content in html

#
# lost_password
#
def test_lost_password_form(test_client):
    rv = test_client.get("/-/lost_password")
    assert rv.status_code == 200

def test_lost_password_mail(app_with_user, test_client, req_ctx):
    # workaround since MAIL_SUPPRESS_SEND doesn't work as expected
    app_with_user.test_mail.state.suppress = True
    # record outbox
    with app_with_user.test_mail.record_messages() as outbox:
        assert len(outbox) == 0
        rv = test_client.post(
            "/-/lost_password",
            data={
                "email": "mail@example.org",
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200
        assert len(outbox) == 1
        assert "Password Recovery" in outbox[0].subject
        assert "/-/recover_password/" in outbox[0].body
        assert "mail@example.org" in outbox[0].recipients

#
# register
#
def test_register_and_login(app_with_user, test_client, req_ctx):
    app_with_user.config["EMAIL_NEEDS_CONFIRMATION"] = False
    app_with_user.config["AUTO_APPROVAL"] = True
    # workaround since MAIL_SUPPRESS_SEND doesn't work as expected
    app_with_user.test_mail.state.suppress = True
    email = "mail2@example.org"
    password = "1234567890"

    rv = test_client.post(
        "/-/register",
        data={
            "email": email,
            "name": "Example User",
            "password1": password,
            "password2": password,
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # test login with new account
    rv = test_client.post(
        "/-/login",
        data={
            "email": email,
            "password": password,
        },
        follow_redirects=True,
    )
    html = rv.data.decode()
    assert "You logged in successfully." in html

def test_register_and_confirm(app_with_user, test_client, req_ctx):
    app_with_user.config["EMAIL_NEEDS_CONFIRMATION"] = True
    # workaround since MAIL_SUPPRESS_SEND doesn't work as expected
    app_with_user.test_mail.state.suppress = True
    # record outbox
    with app_with_user.test_mail.record_messages() as outbox:
        email = "mail3@example.org"
        password = "1234567890"
        assert len(outbox) == 0
        rv = test_client.post(
            "/-/register",
            data={
                "email": email,
                "name": "Example User",
                "password1":password,
                "password2":password,
            },
            follow_redirects=True,
        )
        assert rv.status_code == 200

        # check if account is unconfirmed
        rv = test_client.post(
            "/-/login",
            data={
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        html = rv.data.decode()
        assert "You logged in successfully." not in html

        # check mail
        assert len(outbox) == 1
        assert "confirm" in outbox[0].subject.lower()
        assert "/-/confirm_email/" in outbox[0].body
        assert email in outbox[0].recipients
        # find token
        token = re.findall("confirm_email/(.*)", outbox[0].body)[0]
        # check if confirm token works
        rv = test_client.get(
            "/-/confirm_email/{}".format(token),
            follow_redirects=True,
        )
        assert rv.status_code == 200
        assert "Your email address has been confirmed. You can log in now." in rv.data.decode()
        # check if account is confirmed now
        rv = test_client.post(
            "/-/login",
            data={
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        html = rv.data.decode()
        assert "You logged in successfully." in html

def test_register_errors(app_with_user, test_client, req_ctx):
    # test invalid mail
    rv = test_client.post(
        "/-/register",
        data={
            "email": "john",
            "name": "",
            "password1": "",
            "password2": "",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "email address is invalid" in rv.data.decode()
    assert "account has been created" not in rv.data.decode()
    assert "account is waiting for approval" not in rv.data.decode()
    # test existing email
    rv = test_client.post(
        "/-/register",
        data={
            "email": "mail@example.org",
            "name": "",
            "password1": "",
            "password2": "",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "already registered" in rv.data.decode()
    assert "account has been created" not in rv.data.decode()
    assert "account is waiting for approval" not in rv.data.decode()
    # empty name
    rv = test_client.post(
        "/-/register",
        data={
            "email": "mail@example.com",
            "name": "",
            "password1": "",
            "password2": "",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "enter your name" in rv.data.decode()
    assert "account has been created" not in rv.data.decode()
    assert "account is waiting for approval" not in rv.data.decode()
    # passwords not match
    rv = test_client.post(
        "/-/register",
        data={
            "email": "mail@example.com",
            "name": "John Doe",
            "password1": "123456789",
            "password2": "12345678",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "passwords do not match" in rv.data.decode()
    assert "account has been created" not in rv.data.decode()
    assert "account is waiting for approval" not in rv.data.decode()
    # passwords not match
    rv = test_client.post(
        "/-/register",
        data={
            "email": "mail@example.com",
            "name": "John Doe",
            "password1": "1234567",
            "password2": "1234567",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "password must be at least" in rv.data.decode()
    assert "account has been created" not in rv.data.decode()
    assert "account is waiting for approval" not in rv.data.decode()
