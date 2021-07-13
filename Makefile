include ~/.config/oc-tools.env
export

setup:
	python3 -m pip install --user -r requirements.txt

dev:
	FLASK_APP=oc_stats.app python3 -m flask run

update-data:
	python3 -m oc_stats.update

.PHONY: dev setup
