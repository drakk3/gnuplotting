
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

env = build/venv
python_dev_bin = $(env)/$(PYTHON)/bin
python_dev = $(python_dev_bin)/python
wheel_dev = $(python_dev_bin)/wheel
pip_dev = $(python_dev_bin)/pip
py_src = gnuplotting/*.py

$(python_dev):
	pip install --user 'virtualenv>=15.1.0'
	virtualenv --no-site-packages $(env)/$(PYTHON) --python=$(PYTHON)

$(wheel_dev): $(python_dev) $(pip_dev)
	$(pip_dev) install -r requirements.txt

venv: $(python_dev) $(wheel_dev)

test: venv $(py_src)
	$(python_dev) -B setup.py test $(args)

dist_dev: test
	$(python_dev) -B setup.py bdist_wheel $(args)

install_dev: dist_dev
	$(python_dev) setup.py install $(args)

dist:
	python setup.py bdist_wheel $(args)

install: dist
	python setup.py install $(args)

clean:
	rm -f build dist __pycache__
