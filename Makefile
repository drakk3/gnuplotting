
# Copyright (C) 2017-2018 Romain CHÂTEL <rchastel@protonmail.com>
# This file is part of Gnuplotting.
#
# Gnuplotting is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Gnuplotting is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Gnuplotting.  If not, see <http://www.gnu.org/licenses/>.


args = $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(args):;@:)

python = build/venv/bin/python
wheel = build/venv/bin/wheel
pip = build/venv/bin/pip
py_src = gnuplotting/*.py

$(python):
	pip install --user 'virtualenv>=15.1.0'
	virtualenv --no-site-packages build/venv

$(wheel): $(python) $(pip)
	$(pip) install -r requirements.txt

venv: $(python) $(wheel)

test: venv $(py_src)
	$(python) setup.py test $(args)

dist: test
	$(python) setup.py bdist_wheel $(args)

doc: venv README.org $(py_src)
	$(python) org-doc.py -m README.org -i 'gnuplotting/**.py' -o doc
