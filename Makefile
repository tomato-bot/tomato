publish:
	cd tomato-lib/ && python3 setup.py sdist upload -r pypi
	cd pytest-tomato/ && python3 setup.py sdist upload -r pypi
