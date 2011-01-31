# rfser

Really Fucking Simple Expense Reports

# requirements

* PostgreSQL 8+
* PCRE (apt-get install libpcre3 libpcre3-dev)
* uwsgi
* nginx 
* setuptools / pip / virtualenv
* Python requirements (see REQUIREMENTS)

# building

* cd .. && virtualenv --distribute rfser
* . bin/activate
* pip install -r REQUIREMENTS
* mkdir pkg && cd pkg
* wget http://projects.unbit.it/downloads/uwsgi-0.9.5.4.tar.gz
* tar xzvf uwsgi-0.9.5.4.tar.gz
* cd uwsgi-0.9.5.4
* make
* cp uwsgi $VIRTUAL_ENV/bin/
* cd ..
* wget http://nginx.org/download/nginx-0.8.49.tar.gz
* tar xzvf nginx-0.8.49.tar.gz 
* cd nginx-0.8.49/
* ./configure --with-http_ssl_module
* make
* mv objs/nginx $VIRTUAL_ENV/bin/nginx
* cd $VIRTUAL_ENV
* mkdir logs
* mkdir tmp
* mkdir sock 
* mkdir pid
* cp $VIRTUAL_ENV/pkg/nginx-0.8.49/conf/uwsgi_params etc/


