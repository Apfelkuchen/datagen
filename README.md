## datagen.py 
This script generates either random data or data using the functions (sin,cos ortanh) and timestamps for CouchDB. Simply specify a server and a database and then the script will ask you, which devices and functions you would like to add.

# validation

When the CouchDB has a server admin, the validate.py script has to be executed before the datagenerator is started.

With admin user inputs, it creates a new user: the device and creates a database for it, in which the device is a db_admin (has rights to change design documents)

The datagenerator then creates a _design/auth document in which it allows only admins and hisself to add or change documents

# a more lucid version of the view used in the script is in the folder views
