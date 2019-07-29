#!/usr/bin/python
##
## Verify the log file searching for incorrect login and make a report (csv) then send it by email
## Leandro Fabris Milani - May 2019
##
import sys
import time
import telnetlib
import re
import os
import csv
import subprocess
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Function that use tail command from linux to tail 2M lines from the log file
def tail(f, n=2000000, offset=0):
	offset_total = str(n+offset)
	proc = subprocess.Popen(['tail', '-n', offset_total, f], stdout=subprocess.PIPE)
	lines = proc.stdout.readlines()
	return lines

# Function to send the csv file by email
def sendEmail(filename):
	subject = "Incorrect Logins Report (Radius-Master)"
	body = "Attached .csv file"
	sender_email = "no-reply@email.com"
	password = "password"
	recipients = ['user1@email.com','user2@email.com']

	# Create a multipart message and set headers
	message = MIMEMultipart()
	message["From"] = sender_email
	message["To"] = ", ".join(recipients)
	message["Subject"] = subject
	#message["Bcc"] = receiver_email  # Recommended for mass emails

	# Add body to email
	message.attach(MIMEText(body, "plain"))

	# Open PDF file in binary mode
	with open(filename, "rb") as attachment:
	    # Add file as application/octet-stream
	    # Email client can usually download this automatically as attachment
	    part = MIMEBase("application", "octet-stream")
	    part.set_payload(attachment.read())

	# Encode file in ASCII characters to send by email    
	encoders.encode_base64(part)

	# Attach the file
	part.add_header('Content-Disposition', 'attachment', filename=filename)
    

	# Add attachment to message and convert message to string
	message.attach(part)
	text = message.as_string()

	# Log in to server using secure context and send email
	#context = ssl.create_default_context()
	server = smtplib.SMTP('smtp.mhnet.com.br: 587')
	server.login(sender_email, password)
	server.sendmail(sender_email, recipients, text)

# Main function
def main():
	csvname = "IncorrectLogins-Radius.csv"
	logfile = "/var/log/freradius/radius.log"
	regex_mac = r'[a-fA-F0-9:]{17}'

	# Check if the file exists before execute
	if os.path.exists(csvname):
		os.remove(csvname)

	# Init the array
	array_users = []

	# Get the lines using the function tail
	file = tail(logfile)
	for line in file:
		# Search for 'Login incorrect' each line
		incorrect = re.findall('Login incorrect',line)
		if incorrect:
			# Check if this line contains a mac address
			mac = re.findall(regex_mac,line)
 			if mac:
   				splituser1 = line.split('[')[1]
				user = splituser1.split('/')[0]
				# Check if the second part of split is a mac address (avoid wireless requisitions that use mac instead username)
				usermac = re.findall(regex_mac,user)
				if not usermac:
					csv_estruct = user + ';' + mac[0]
					array_users.append(csv_estruct)
	
	# Remove duplicates entry from array
	lista_unicos = dict.fromkeys(array_users).keys()
	
	# Open the file to write the lines
	csvfile = open(csvname, "w")
	listUsers = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
	
	# Write each line
	for linha in lista_unicos:
		listUsers.writerow([linha])
	# Close file
	csvfile.close()

	# Send the file by email
	sendEmail(csvname)

	# Remove the file
	if os.path.exists(csvname):
		os.remove(csvname)

if __name__ == '__main__':
    main()