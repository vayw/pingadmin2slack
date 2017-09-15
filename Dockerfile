FROM python:3-alpine
ADD slackproxy.py /
ADD slackwebhook.py /
ENTRYPOINT [ "/usr/local/bin/python3.6m", "./slackproxy.py" ] 
CMD ["--pingadmin-apikey='CHANGEME'", "--pingadmin-answer='CHANGEME'", "--slackurl='CHANGEME'" ]
