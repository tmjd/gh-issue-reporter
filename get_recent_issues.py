#!/usr/bin/python

from datetime import timedelta, date
import github3
import pprint
from getpass import getuser, getpass

CREDENTIALS_FILE='/home/tomjoad/.check_issue_creds'

try:
    # Python 2
    prompt = raw_input
except NameError:
    # Python 3
    prompt = input


gh = None
auth = None
try:
    with open(CREDENTIALS_FILE, 'r') as fd:
        token = fd.readline().strip()
        id = fd.readline().strip()
        gh = github3.login(token=token)
except:
    gh = None
    print "Failed to load credentials file"


def my_two_factor_function():
    code = ''
    while not code:
        # The user could accidentally press Enter before being ready,
        # let's protect them from doing that.
        code = prompt('Enter 2FA code: ')
    return code

if gh is None:
    user = raw_input("Please enter GitHub name: ")
    pw = ''
    while not pw:
        pw = getpass('Password for {0}: '.format(user))

    scopes = []
    note = 'issue-status reporter'
    note_url = 'http://pushmepullme.net'
    auth = github3.authorize(user, pw, scopes, note, note_url, client_id='', client_secret='', two_factor_callback=my_two_factor_function)
    with open(CREDENTIALS_FILE, 'w') as fd:
        fd.write(auth.token + '\n')
        fd.write("{0}".format(auth.id))
    gh = github3.login(token, auth.token)

print "Rate limit info {0}".format(gh.rate_limit()['rate']['remaining'])

start = date.today() - timedelta(days=80)
while start.weekday():
    start = start + timedelta(days=1)

info = []
while start < (date.today()-timedelta(days=7)):
    end = start + timedelta(days=7)
    info.append({'start':start, 'end':end, 'count':0, 'opened':0, 'closed':0})
    start = end

info.append({'start':start, 'end':date.today(), 'count':0, 'opened':0, 'closed':0})

for repo in gh.iter_user_repos("projectcalico"):
    #print "stuff {0}".format(repo)
    for issue in repo.iter_issues(state='all', labels='kind/support'):
        #print "  issue {0} = {1} - {2}".format(issue, issue.created_at, issue.closed_at)
        for ent in info:
            if (issue.created_at.date() < ent['end']) and ((issue.closed_at is None) or (issue.closed_at.date() > ent['end'])):
                ent['count'] = ent['count'] + 1
            if issue.created_at.date() >= ent['start'] and issue.created_at.date() <= ent['end']:
                ent['opened'] = ent['opened'] + 1
            if (issue.closed_at is not None) and (issue.closed_at.date() >= ent['start']) and (issue.closed_at.date() <= ent['end']):
                ent['closed'] = ent['closed'] + 1

for ent in info:
    print "{0} had {1} +{2} -{3}".format(ent['end'].strftime("%a %Y-%m-%d"), ent['count'], ent['opened'], ent['closed'])
