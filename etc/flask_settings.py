import datetime

PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=2)
SESSION_COOKIE_NAME = "ttabler_web"
SECRET_KEY = '\xc0\xdd\x1e\xff+/>3\xec\xacn\xfc\x06\x9b\x07\x8e,\xe2\xd4\x14\xe7\xbc?\xe6'
SQLALCHEMY_DATABASE_URI = 'sqlite:////var/lib/ttabler-web/ttabler-web.sqlite'
