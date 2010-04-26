"""sauce.py: this is the backend code"""
import json
import os

from bottle import route, run as run_bottle, request, response, send_file, abort
from pyhackerstories import get_stories
from twill.commands import go, showlinks, formvalue, submit, reset_browser

ROOT_DIR = os.path.realpath(os.path.dirname(__file__))
HN_URL = "http://news.ycombinator.com/"

@route('/')
def index():
    """this is the index"""
    return send_file('index.html', ROOT_DIR)

@route('/hn', method='GET')
def get_all_stories():
    """hackernews json data"""
    data = list()

    # get the page (every page has 30 stories)
    try:
        page = int(request.GET.get('page', '').strip())
    except ValueError:
        page = 1

    # how many stories we want for the page
    try:
        counter = int(request.GET.get('stories', '').strip())
    except ValueError:
        counter = 30 

    # we check if we want to see the new stories
    if request.GET.get('new', '').strip() == 'true':
        new = True
    else:
        new = False

    # we finally fetch the stories
    stories = get_stories(page, new)

    # iterate over the stories and add them to the list
    for story in stories[:counter]:
        data.append(story.__dict__)

    # needed to do this, because data is a list and bottle
    # supports autojson with dicts only
    response.content_type = 'application/json'
    return json.dumps(data)

@route('/hn/:hn_id', method='POST')
def vote_story(hn_id):
    """vote for an story"""
    vote = request.POST.get('vote', '').strip()

    # we need a voting direction "up" or "down"
    if vote == '' or (vote != 'up' and vote != 'down'):
        return abort(code=400, text="Invalid voting direction, " +
                                    "needs to be 'up' or 'down'?")

    # check for the http auth
    if not request.auth:
        return abort(code=401, text="We need your username and " +
                                "password for this operation.")

    # i can haz your hn password
    username, password = request.auth

    # we start web scraping
    go(HN_URL)

    # lets find the login url
    login_url = ''
    for link in showlinks():
        if link.text == "login":
            login_url = link.url

    go(login_url)

    # we login #1 is the form (login, #2 is register)
    formvalue('1', 'u', username)
    formvalue('1', 'p', password)

    # 4 is the position of the submit button
    submit('4') 

    # now we go to the story
    go('/item?id=%s' % hn_id)

    # and vote for it
    # find the link
    voting_url = ''
    for link in showlinks():
        if link.url.startswith('vote?for=%s&dir=%s&by=%s' % 
                                (hn_id, vote, username)):
            voting_url = '/' + link.url

    if voting_url == '':
        return abort(code=400, text="Something's wrong at voting, " +
                                    "Could not find the voting url. " +
                                    "Most likely you already voted or " +
                                    "the username or password are wrong.")
    go(voting_url)

    # lets find the login url
    for link in showlinks():
        if link.text == "logout":
            logout_url = link.url

    go(HN_URL)
    go(logout_url)

    # and we're done!
    reset_browser()

    # success! response is always in JSON
    return {'status': "ok", 'message': "voted successfully for %s" % hn_id}

if __name__ == '__main__':
    run_bottle(host='localhost', port=8080)
