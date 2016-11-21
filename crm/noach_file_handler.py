from bs4 import BeautifulSoup
def noach_file_handler(noach_file):
	''' takes a django InMemoryUploadedFile and returns a dictionary with noach ID as a key and a dict as a value,
	there is patient data in internal dict such as first name, last name, phone number and audiograms'''
	
	soup = BeautifulSoup(noach_file, "html.parser")
	patients = {}
	for i in soup.find_all('pt:patient'):
		if i.find('pt:patient'):
			continue
		else:
			patient = {}
			noahpatientid = int(i.find('pt:noahpatientid').text)
			patient['noahpatientid'] = noahpatientid
            
			noachcreatedate = i.find('pt:createdate').text
			patient['noachcreatedate'] = noachcreatedate
            
			first_name = i.find('pt:firstname').text
			patient['first_name'] = first_name
			
			last_name = i.find('pt:lastname').text
			patient['last_name'] = last_name

			gender = i.find('pt:gender').text

			if i.find('pt:dateofbirth'):
				dateofbirth = i.find('pt:dateofbirth').text
				patient['dateofbirth'] = dateofbirth
            
			if i.find('pt:homephone').text:
				homephone = i.find('pt:homephone').text
				patient['homephone'] = int(homephone)
            
			if i.find('pt:workphone').text:
				workphone = i.find('pt:workphone').text
				patient['workphone'] = int(workphone)
            
			if i.find('pt:mobilephone').text:
				mobilephone = i.find('pt:mobilephone').text
				patient['mobilephone'] = int(mobilephone)
            
			action = i.find_all('pt:action')
			for y in action:
				type_of_data = y.find('pt:typeofdata')
				if str(type_of_data.text) == 'Audiogram':
					last_audiogram = {}
					time_of_test = y.find('pt:actiondate').text
					last_audiogram['time_of_test'] = time_of_test
					a = y.find_all('tonethresholdaudiogram')
					results = {}
					for tt in a:
						stimulussignaloutputs = tt.find_all('stimulussignaloutput')
						for x in stimulussignaloutputs:
							results[str(x.text)] = {}
						tonepoints = tt.find_all('tonepoints')
						for z in tonepoints:
							stimulusfrequency = int(z.find('stimulusfrequency').text)
							stimuluslevel = int(str(z.find('stimuluslevel').text).replace('.0', ''))
							results[x.text][stimulusfrequency] = stimuluslevel
					last_audiogram['results'] = results
					patient['last_audiogram'] = last_audiogram
            
			patients[noahpatientid]=patient
	return patients
