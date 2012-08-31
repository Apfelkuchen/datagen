import couchdb
import getpass

admin = raw_input("Enter admin name: \n> ")
passwd = getpass.unix_getpass("Enter admin password: \n> ")

serveraddress = raw_input("Enter server address: "+'\n> ')
if not serveraddress:
	serveraddress = 'http://localhost:5984'

deviceID = raw_input("Enter deviceID: "+'\n> ')
devicePWD = raw_input("Chose a device password: "+'\n> ')

Server = couchdb.Server(serveraddress)
Server.resource.credentials=(admin,passwd)

userdb = Server['_users']

# create user
try:
	userdoc = userdb['org.couchdb.user:'+deviceID]
	print "user already exists"
except couchdb.ResourceNotFound:
	userdoc = {"_id" : "org.couchdb.user:"+deviceID, "name" : deviceID, "password" : devicePWD, "type" : "user", "roles" : []}
	userdb.save(userdoc)
	print('new user created: '+deviceID)

# create database

try:
	db = Server[deviceID]
	print('Database already exists')

except couchdb.ResourceNotFound:
	db = Server.create(deviceID)
	print('new database created: '+deviceID)

# create security, only admins and the deviceID user may edit design documents and other security documents
try:
	secdoc = db['_security']
	secdoc["_id"] = '_security'
	secdoc['admins'] = { "names" : [deviceID], "roles" : ["_admin"]}
	secdoc['members'] = { "names" : [], "roles" :  []}
	db.save(secdoc)
except KeyError:
	pass

# create or edit the authentication doc, that only admins and the deviceID user can create new and edit documents
try:
	authdoc = db['_design/auth']
	print('validation doc found')
except KeyError:
	authdoc = { "_id" : "_design/auth"}
	print('validation doc created')
	
authdoc['language'] = 'javascript'
authdoc["validate_doc_update"] = "function(newDoc, oldDoc, userCtx) {   if (userCtx.roles.indexOf('_admin') !== -1 || userCtx.name == '"+deviceID+"' ) {     return true;   } else { throw({forbidden: 'Only admins may edit the database'});   } }"
db.save(authdoc)
	



