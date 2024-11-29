import os
import requests


def send_email(to_email: str, subject: str, body: str) -> None:
	MAILGUN_API_BASEURL = 'https://api.eu.mailgun.net/v3/' + os.environ['MAILGUN_DOMAIN']
	# Send email
	return requests.post(
		MAILGUN_API_BASEURL + "/messages",
		auth=("api", os.environ['MAILGUN_API_KEY']),
		data={
            "from": "%s <%s>" % (os.environ['MAILGUN_FROM_NAME'], 'no-reply@' + os.environ['MAILGUN_DOMAIN']),
			"to": [to_email],
			"subject": subject,
			"text": body
        },
    )
