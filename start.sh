killall uwsgi
killall nginx
BASE=.
bin/nginx -p $BASE -c etc/nginx.conf
bin/uwsgi -d logs/uwsgi.log -p 4 -s sock/uwsgi.sock -H $BASE rfser.py

