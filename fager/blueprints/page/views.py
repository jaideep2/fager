from flask import Flask, redirect, url_for, session, request, Blueprint, flash, render_template
from flask_oauth import OAuth
from fager.blueprints.page.forms import PostForm
import requests
from config.settings import FB_ACCESS_TOKEN, SECRET_KEY, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, PAGE_ID

page = Blueprint('page', __name__, template_folder='templates')

oauth = OAuth()

globalDrafts = ['183366078885902_184536722102171']


facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email,manage_pages,publish_pages'}
)


@page.route('/')
def index():
    return redirect(url_for('page.login'))


@page.route('/login')
def login():
    return facebook.authorize(callback=url_for('page.facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True))


@page.route('/login/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    #session['oauth_token'] = (resp['access_token'], '')
    session['oauth_token'] = (FB_ACCESS_TOKEN, '')
    me = facebook.get('/me')
    status = 'Logged in as id=%s name=%s redirect=%s' % \
        (me.data['id'], me.data['name'], request.args.get('next'))
    return redirect(url_for('page.post'))


@page.route('/login/authorized/post', methods=['GET', 'POST'])
def post():
    form = PostForm()
    if request.method == 'POST':
        thepost = request.form['update']
        if request.form['submit'] == 'draft':
            draft_to_FB(thepost)
        else:
            sch_post_to_FB(thepost)
    posts = get_FB_posts()
    drafts = get_FB_drafts()
    #metrics = get_FB_metrics(posts)
    metrics = 0
    return render_template('page/home.html', form=form, posts=posts, drafts=drafts, metrics=metrics)


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


def get_FB_metrics(posts):
    metrics = {}
    access_token = get_facebook_oauth_token()[0]
    metricType = 'post_impressions'
    for post in posts:
        postid = post['id']
        url = "https://graph.facebook.com/v2.11/" + postid + "/insights/" + metricType + "?access_token=" + access_token
        r = requests.get(url)
        metrics[postid] = r.json()['data'][0]['values'][0]['value']
    return metrics


def get_FB_drafts():
    access_token = get_facebook_oauth_token()[0]
    drafts = []
    for id in globalDrafts:
        url = "https://graph.facebook.com/v2.11/" + id + "?access_token=" + access_token
        r = requests.get(url)
        drafts.append(r.json())
    return drafts

def get_FB_posts():
    access_token = get_facebook_oauth_token()[0]
    url = "https://graph.facebook.com/v2.11/"+PAGE_ID+"/feed?access_token=" + access_token
    r = requests.get(url)
    return r.json()['data']


def draft_to_FB(thepost):
    access_token = get_facebook_oauth_token()[0]
    thepost.replace(' ', '+')
    url = "https://graph.facebook.com/v2.11/" + PAGE_ID + "/feed?published=false&message=" + thepost + "&access_token=" + access_token
    r = requests.post(url)
    global globalDrafts
    globalDrafts.append(r.json()['id'])


def post_to_FB(thepost):
    access_token = get_facebook_oauth_token()[0]
    thepost.replace(' ', '+')
    url = "https://graph.facebook.com/v2.11/"+PAGE_ID+"/feed?message=" + thepost + "&access_token=" + access_token
    r = requests.post(url)
    print r.status_code, r.reason, r.text

def sch_post_to_FB(thepost,time=None):
    '''
    https://graph.facebook.com/546349135390552/feed?
      published=false&amp;
      message=An scheduled post&
      scheduled_publish_time=1429134465
    '''
    import datetime
    dt = datetime.datetime.now() + datetime.timedelta(hours=2)
    schTime = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
    access_token = get_facebook_oauth_token()[0]
    thepost.replace(' ', '+')
    url = "https://graph.facebook.com/v2.11/" + PAGE_ID + "/feed?published=false&message=" + thepost + "&scheduled_publish_time="+ str(int(schTime)) +"&access_token=" + access_token
    print url
    r = requests.post(url)
    print r.status_code, r.reason, r.text