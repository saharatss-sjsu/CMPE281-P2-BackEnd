#!/bin/bash
cd $(dirname "$0")
cd ../..
zip -r server_backend.zip CMPE281-P2-Backend -i \
	"CMPE281-P2-Backend/apps/*" \
	"CMPE281-P2-Backend/Backend/*" \
	"CMPE281-P2-Backend/credentials/mysql.cnf" \
	"CMPE281-P2-Backend/setup/*.service" \
	"CMPE281-P2-Backend/setup/requirements.txt" \
	"CMPE281-P2-Backend/manage.py" \

