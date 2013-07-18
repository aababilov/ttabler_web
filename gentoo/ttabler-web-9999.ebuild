# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="5"

PYTHON_DEPEND="2"
SUPPORT_PYTHON_ABIS="1"
RESTRICT_PYTHON_ABIS="2.4 3.*"
DISTUTILS_SRC_TEST="nosetests"

inherit eutils distutils git-2

MY_PN="ttabler-web"
MY_P="${MY_PN}-${PV}"

DESCRIPTION="A web interace to ttabler"
HOMEPAGE="https://github.com/aababilov/ttabler_web"
EGIT_REPO_URI="git://github.com/aababilov/ttabler_web.git"

LICENSE="GPL-3"
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE=""

RDEPEND="dev-python/flask
	dev-python/setuptools
	dev-python/flask-sqlalchemy"
DEPEND="${RDEPEND}"

S="${WORKDIR}/${MY_P}"

PYTHON_MODNAME="ttabler_web"


pkg_setup() {
	enewgroup ttabler-web
	enewuser ttabler-web -1 -1 /var/lib/ttabler-web ttabler-web

	python_pkg_setup
}

src_install() {
	distutils_src_install

	local gentoodir="${WORKDIR}/${GDM_EXTRA}"

	# log, etc.
	keepdir /var/{lib,log}/ttabler-web
	fowners -R ttabler-web:ttabler-web /var/{lib,log}/ttabler-web
	fperms 775 /var/{lib,log}/ttabler-web
}
