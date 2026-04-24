config:
	python main.py config set

auth:
	python main.py auth

tui:
	python main.py tui

upload:
	rm -rf dist && python -m build  && twine upload dist/*
