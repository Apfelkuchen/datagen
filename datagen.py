import couchdb
import math
import time								# to create a timestamp and timouts
from random import uniform				# random float between a and b: uniform(a,b)
from thread import start_new_thread		# new thread, usefull for a changesfeed listener

class Skeleton:
	def __init__(self, server = 'http://localhost:5984', database = 'datagenerator'): 
		self.Server = couchdb.Server(server)
		# for validation: 
		self.deviceID = 'datagenerator'
		self.password = '12345678'
		self.Server.resource.credentials=(self.deviceID,self.password)
#		try:
#			self.db = self.Server[database]
#		except couchdb.ResourceNotFound:
#			self.db = self.Server.create(database)
#			print('new database created: '+database)

		self.db = self.Server[database]
		self.ParDoc = []
		
		newest = self.db.changes()['last_seq']
		self.changesfeed = self.db.changes(feed='continuous', heartbeat='1000', include_docs=True, since=newest, filter='Skeleton/parameter')
			
	def createView(self):
		# this function adds two views called bykey and bytime to the selected database, the views are written in javascript and are given to python in the JSON format
		# bykey is for a list of available devices
		# bytime is usefull for plotting
		# the Parameter filter shows only docs with the _id = Parameter to the changesfeed
		# the following is written with a CouchApp and then copied from Futon, excuse the impossible readability, a more lucid version for couchapps is in the folder views
		try:
			designdoc = self.db['_design/Skeleton']
		except couchdb.ResourceNotFound:
			designdoc = {"_id" : "_design/Skeleton"}
			print('new designdoc created')

			designdoc['views'] = { "bykey": {"map": "function(doc) {\n\tfor(var i in doc) {\n\t\tfor(var j in doc[i]) {\n\t\t\tif(doc[i][j].time) {\n\t\t\t\tfor(var key in doc[i][j]) {\n\t\t\t\t\tvar k = key.replace('#','');\n\t\t\t\t    \tk = k.replace('.','');\n\t\t\t\t    \tk = k.replace(',',' ');\n\t\t\t\t\t\tk = k.replace(/^\\\\s+|\\\\s+$/g, '');\n\t\t\t\t\temit([i,j,k], doc[i][j][key]);\n}}}}}",\
		       "reduce": "function(keys, values, rereduce) {\n  if (rereduce) {\n    return sum(values);\n  } else {\n    return values.length;\n  }\n}"\
		   		},\
		   "bytime": {\
		       "map": "function(doc) {\n\tfor(var i in doc) {\n\t\tfor(var devicename in doc[i]) {\n\t\t\tif(doc[i][devicename].time) {\n\t\t\t\temit([i,devicename,doc[i][devicename]['time']], doc[i][devicename]['data']);\n}}}}",\
		       "reduce": "function(keys, values, rereduce) {\n\tvar tot = 0;\n\tvar count = 0;\n\tif (rereduce) {\n\t\tfor (var idx in values) {\n\t\t\ttot += values[idx].tot;\n\t\t\tcount += values[idx].count;\n\t\t\t}\n\t\t}\n\telse {\n\t \ttot = sum(values);\n\t\tcount = values.length;\n\t\t\n\t}\n\treturn {tot:tot, count:count, avg:tot/count};\n}"}}
		
		designdoc['filters'] = {"parameter" : "function(doc, req) {if(doc._deleted == true) {return false;} if(doc._id == 'Parameter') {return true;} return false;}"}
		self.db.save(designdoc)
		print('view and filter created')
		
		# create a validation document, which only allows this device and admins to change database
		try:
			valdoc =self.db['_design/auth']
		except couchdb.ResourceNotFound:
			valdoc = {"_id" : "_design/auth"}
			print('new validation doc created')
		
		valdoc['language'] = 'javascript'
		valdoc["validate_doc_update"] = "function(newDoc, oldDoc, userCtx) {   if (userCtx.roles.indexOf('_admin') !== -1 || userCtx.name == '"+self.deviceID+"' ) {     return true;   } else { throw({forbidden: 'Only admins may edit the database'});   } }"
		self.db.save(valdoc)
		
	def startUp(self):
	## Checks if there is already a Parameter Doc, if not it creates one
		if 'Parameter' in self.db:
			self.ParDoc = self.db['Parameter']
		
		else:
			self.NewParDoc()
			
	def NewParDoc(self):
	## Creates a new Parameter Document with inputs of the user
		self.ParDoc = {"_id" : "Parameter"}
		print('Types of Test Devices, seperated by comma (e.g. adcs, meters, etc) : \n')
		types = raw_input("> ")
		if not types:
			types = "devices,adcs,meters"
		types=types.replace(' ','')
		types=types.split(',')
		types = set(types) # remove multiple entries

		for t in types:
			print('Name of Test Devices for ' + t + ', seperated by comma\n')
			y = raw_input("> ")
			if not y:
				y = 'device1,device2,device3'
			y=y.replace(' ','')
			y=y.split(',')
			y=set(y)
			self.ParDoc[t]={}
			for i in y:
				print('Function for device: '+i+', (sin,cos,tanh or random)\n')
				dfun = raw_input("> ")
				if not dfun:
					dfun = 'sin'
				if (dfun=='sin' or dfun=='cos' or dfun=='tanh'):
					damp = raw_input("Amplitude for device: "+i+'\n> ')
					if not damp:
						damp = 1.
					damp=float(damp)
					dfreq= raw_input("Frequency for device: "+i+'\n> ')
					if not dfreq:
						dfreq = 0.01
					dfreq= float(dfreq) 
					self.ParDoc[t][i]={}
					self.ParDoc[t][i]['amplitude']= damp
					self.ParDoc[t][i]['frequency']= dfreq
				if (dfun =='random'):
					mean = raw_input("Expected value for random distribution for device: "+i+"\n> ")
					if not mean:
						mean = 0
					mean=float(mean)
					spread = raw_input("Spread for random distribution for device: "+i+"\n> ")
					if not spread:
						spread = 1
					spread=float(spread)
					self.ParDoc[t][i]={}
					self.ParDoc[t][i]['mean']= mean
					self.ParDoc[t][i]['spread']= spread
				
				self.ParDoc[t][i]['function']= dfun
					
		self.ParDoc['mode'] = 'on'
		self.db.save(self.ParDoc)
	
	def ChangesFeed(self):
		for line in self.changesfeed:
			self.ParDoc = line['doc']
			print 'New Parameter'
			
	def DataGen(self):
		self.createView()
		self.startUp()
		start_new_thread(self.ChangesFeed,()) # uses a simultanous thread for listening to the changesfeed
		while True:
			newdoc = {'mode': 'on'}
			for types in self.ParDoc:
				if (type(self.ParDoc[types])!=str):
					newdoc[types] = {}
					for i in self.ParDoc[types]:
						newdoc[types][i] = {}
						nfun = self.ParDoc[types][i]['function']
						newdoc[types][i]['function'] = nfun
						if (nfun == 'sin' or nfun == 'cos' or nfun == 'tanh'): 
							try: 
								namp = self.ParDoc[types][i]['amplitude']
								nfreq = self.ParDoc[types][i]['frequency']
							except KeyError:
								self.ParDoc[types][i]= {}
								self.ParDoc[types][i]['function'] = nfun
								self.ParDoc[types][i]['amplitude'] = namp = 1.
								self.ParDoc[types][i]['frequency'] = nfreq = 1.
								self.db.save(self.ParDoc)
							newdoc[types][i]['amplitude'] = namp
							newdoc[types][i]['frequency'] = nfreq
							newdoc[types][i]['time']= time.time()
							newdoc[types][i]['data']= namp*self.Functions(nfun,nfreq*newdoc[types][i]['time'])
								
						if (nfun == 'random'):
							try: 
								nmean = self.ParDoc[types][i]['mean']
								nspread = self.ParDoc[types][i]['spread']
							except KeyError:
								self.ParDoc[types][i]= {}
								self.ParDoc[types][i]['function'] = nfun
								self.ParDoc[types][i]['mean'] = nmean = 0.
								self.ParDoc[types][i]['spread'] = nspread = 1.
								self.db.save(self.ParDoc)
							newdoc[types][i]['mean'] = nmean
							newdoc[types][i]['spread'] = nspread
							newdoc[types][i]['time']= time.time()
							newdoc[types][i]['data']= uniform(-nspread/2,nspread/2)+nmean
			self.db.save(newdoc)
			print 'Newdoc created'
			# time.sleep(1)     # to change the update frequency
	
	def Functions(self, function = 'sin', x=1):
		## some functions for creating data
		
		if function == 'sin':
			return math.sin(x)
		
		if function == 'cos':
			return math.cos(x)
		
		if function == 'tanh':
			return math.tanh(x)
			
		else:
			return 'Not supported function'

test = Skeleton()
test.DataGen()
		
	
