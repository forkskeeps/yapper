#!/bin/bash
echo -n "Enter FLASK_ENV(dev, prod, test): "
read text
export FLASK_CONFIG="$text"
echo "$FLASK_CONFIG"
gunicorn -w 4 -b 127.0.0.1:8080 application:app
