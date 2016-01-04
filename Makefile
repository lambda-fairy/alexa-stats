alexa-stats.json: alexa-pages/*.html
	@ ./scan.py $^ > $@
