## datagen.py 
This script generates either random data or data using the functions (sin,cos ortanh) and timestamps for CouchDB. Simply specify a server and a database and then the script will ask you, which devices and functions you would like to add.

# validation

the validate.py script must be run before the datagenerator is started, when the CouchDB has a server admin

it creates with admin rights a new user, the device and creates a database for it, in which the device is a db_admin (has rights to change design documents)

the datagenerator then creates a _design/auth document in which it allows only to admins and his self to add or change documents
