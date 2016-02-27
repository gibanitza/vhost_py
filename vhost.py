#!/usr/bin/python

import os, sys, getpass, sh, re
from os import path
import MySQLdb as db


###environment variables

NGINX_CONFIG = '/etc/nginx/sites-available'
NGINX_SITES_ENABLED = '/etc/nginx/sites-enabled'
PHP_INI_DIR = '/etc/php5/fpm/pool.d'
WEB_SERVER_GROUP = 'www-data'
NGINX_INIT = '/etc/init.d/nginx'
PHP_FPM_INIT = '/etc/init.d/php5-fpm'
current_dir = os.getcwd()

### functions

## setup Laravel directories & user
def setupLaravel(domain,username,password):
	siteRoot = '/webapps/%s'%(domain)
	siteLogs = '/webapps/%s/logs'%(domain)
	sitePublic = '/webapps/%s/laravel/public'%(domain)
	larConfTemplate = 'lar.nginx.vhost.conf.template'
	sh.useradd('-m','-d',siteRoot, username,'-s', '/bin/bash','-p', password)
	sh.usermod('-aG', username, WEB_SERVER_GROUP)
	sh.mkdir('-p', siteLogs)
	sh.mkdir('-p', sitePublic)
	sh.cp('index.php', sitePublic)
	sh.chmod('-R','750', siteRoot)
	sh.chmod('-R','770', siteLogs)
	sh.chown('-R',"%s:%s"%(username,username), siteRoot)
	setupNginx(domain,username,larConfTemplate,sitePublic,siteLogs)
	setupPhpFpm(username)

## setup WP directories & user
def setupWP(domain,username,password):
	siteRoot = '/webapps/%s'%(domain)
	siteLogs = '/webapps/%s/logs'%(domain)
	sitePublic = '/webapps/%s/public'%(domain)
	wpConfTemplate = 'wp.nginx.vhost.conf.template'
	sh.useradd('-m','-d',siteRoot, username,'-s', '/bin/bash','-p', password)
	sh.usermod('-aG', username, WEB_SERVER_GROUP)
	sh.mkdir('-p', siteLogs)
	sh.mkdir('-p', sitePublic)
	sh.cp('index.php', sitePublic)
	sh.chmod('-R','750', siteRoot)
	sh.chmod('-R','770', siteLogs)
	sh.chown('-R',"%s:%s"%(username,username), siteRoot)
	setupNginx(domain,username,wpConfTemplate,sitePublic,siteLogs)
	setupPhpFpm(username)

##nginx setup
def setupNginx(domain,username,confTemplate,sitePublic,siteLogs):
	nginxSitesAvailable = '%s/%s'%(NGINX_CONFIG,domain)
	nginxEnabled = '%s/%s'%(NGINX_SITES_ENABLED,domain)
	nginxTemplate = open(confTemplate).read()
	nginxTemplate = nginxTemplate.replace("@@HOSTNAME@@", domain)
	nginxTemplate = nginxTemplate.replace("@@PATH@@", sitePublic)
	nginxTemplate = nginxTemplate.replace("@@LOG_PATH@@", siteLogs)
	nginxTemplate = nginxTemplate.replace("@@SOCKET@@", username)
	nginxConf = open(nginxSitesAvailable, "w")
	nginxConf.write(nginxTemplate)
	nginxConf.close()
	sh.chmod('600', nginxSitesAvailable)
	os.symlink(nginxSitesAvailable, nginxEnabled)
	sh.service("nginx","restart")

##php-fpm setup
def setupPhpFpm(username):
	fpmConfFile = '%s/%s.pool.conf'%(PHP_INI_DIR,domain)
	phpFpmTemplate = open("pool.conf.template").read()
	phpFpmTemplate = phpFpmTemplate.replace("@@USER@@", username)
	phpFpmConf = open(fpmConfFile, "w")
	phpFpmConf.write(phpFpmTemplate)
	phpFpmConf.close()
	sh.service("php5-fpm","restart")

## create DB
def setupDB(rootPass,dbName,dbUser,dbPassword):
	dbConnection = db.connect('localhost','root', rootPass)
	dbCursor = dbConnection.cursor()
	dbCursor.execute("CREATE DATABASE IF NOT EXISTS %s" % (dbName))
	dbCursor.execute("GRANT USAGE ON *.* TO %s@localhost IDENTIFIED BY '%s'" % (dbUser,dbPassword))
	dbCursor.execute("GRANT ALL PRIVILEGES ON %s.* TO %s@localhost" % (dbName,dbUser))
	dbCursor.execute("FLUSH PRIVILEGES")


###getting all the input from the user

## Input for OS/nginx user
domain = raw_input('\n#### Please enter domain/OS data####\nEnter DOMAIN name: ')
username = raw_input('Enter USERNAME (for ssh, scp, sftp): ')
#password verification
usrPassword = lambda: (getpass.getpass('Enter user password: '), getpass.getpass('Retype password: '))
usrPassword1, usrPassword2 = usrPassword()
while usrPassword1 != usrPassword2:
	print('Passwords do not match. Try again')
	usrPassword1, usrPassword2 = usrPassword()

##Input for DB name, DB user & password
dbAdminPass = getpass.getpass('\n!!! Enter DB root password !!!\n ')
dbName = raw_input('\n###Please enter DB data###\nEnter DB name: ')
dbUser = raw_input('Enter DB user: ')
dbPass = lambda: (getpass.getpass('Enter DB password: '), getpass.getpass('Retype password: '))
dbPassword1, dbPassword2 = dbPass()
while dbPassword1 != dbPassword2:
	print('DB passwords do not match. Try again')
	dbPassword1, dbPassword2 = dbPass()

##Check for site version: WP or Laravel
siteType = raw_input('\n\nWordPress[WP] or Laravel[L]: ')
wpressOrLar = ["wp","l"]
while siteType.lower() not in wpressOrLar:
	print( 'Please enter correct value (WP or L):')
	siteType = raw_input('WordPress[WP] or Laravel[L]: ')

#######
# doing some work
#######

## Create user, directories, configuration files etc.

if siteType.lower() == "wp":
	setupWP(domain,username,usrPassword1)
elif siteType.lower() == "l":
	setupLaravel(domain,username,usrPassword1)


## Create DB, user, pass

setupDB(dbAdminPass,dbName,dbUser,dbPassword1)



