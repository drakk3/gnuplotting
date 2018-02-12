
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

cmd = $(word 1,$(MAKECMDGOALS))
$(cmd)_args = $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $($(cmd)_args):;@:)

py_src = gnuplotting/*.py

ifdef DEV_ENV
# DEV part of the Makefile
env_dir = build/env
python_bin = $(env_dir)/$(DEV_ENV)/bin
python = $(python_bin)/python
wheel = $(python_bin)/wheel
pip_dev = $(python_bin)/pip

$(python):
	pip install --user 'virtualenv>=15.1.0'
	virtualenv --no-site-packages $(env_dir)/$(DEV_ENV) --python=$(DEV_ENV)

$(wheel): $(python) $(pip)
	$(pip) install -r requirements.txt

init_env: $(python) $(wheel)


test: init_env $(py_src)
	$(python) -B setup.py test $(test_args)

else
# User part of the Makefile
python ?= python

test:
	$(info Nothing to do)

endif

dist:
	$(python) -B setup.py bdist_wheel $(dist_args)

install: dist
	$(python) -B setup.py install $(install_args)

clean:
	$(RM) -r build dist __pycache__
