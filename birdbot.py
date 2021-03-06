''' let's learn about birds '''
import blacklist
from bs4 import BeautifulSoup
from datetime import datetime
from html import unescape
import json
import os
from PIL import Image
import random
import re
from resizeimage import resizeimage
import requests
import settings
from TwitterAPI import TwitterAPI
from urllib.request import urlretrieve

print('--------- creating fact --------')
print(datetime.today().isoformat())
# pick a bird form the list
line = json.loads(random.choice(open('birdlist').readlines()))
url = line['url']
bird = line['name'][0].lower() + line['name'][1:]
print('bird page: %s' % url)

# download the bird's wikipedia entry
entry = requests.get('http://en.wikipedia.org%s' % url)
soup = BeautifulSoup(entry.text)

scientific = soup.find(class_='binomial').find('i').text

# find thumbnail
src = soup.find(class_='image').find('img')['src']
# compute full sized image url from thumbnail
extension = '.JPG' if '.JPG' in src else '.jpg'
src = src.split(extension)[0] + extension
image_url = 'https:' + re.sub('thumb/', '', src)

# download bird image
filename = re.sub(' ', '-', bird.lower()) + '.jpg'
outpath = os.getcwd() + '/images/%s' % filename
urlretrieve(image_url, outpath)

# resize if necessary
while os.path.getsize(outpath) > 3000000:
    img = Image.open(outpath)
    _, height = img.size
    img = resizeimage.resize_height(img, height / (4/3))
    img.save(outpath, img.format)

# search twitter for the fact
pronouns = ['she ', 'he ']
prompts = [
    'acts like ',
    'doesn\'t ',
    'has ',
    'is just ',
    'is only ',
    'is always ',
    'is never ',
    'is the ',
    'keeps ',
    'loves to ',
    'lives in ',
    'makes ',
    'should really ',
    'takes ',
    'thinks ',
    'tries to ',
    'tends to ',
    'was ',
    'wasn\'t ',
    'will ',
]

pronoun = random.choice(pronouns)
prompt = pronoun + random.choice(prompts)
print('prompt: %s' % prompt)

api = TwitterAPI(settings.API_KEY, settings.API_SECRET,
                 settings.ACCESS_TOKEN, settings.ACCESS_SECRET)
# get tweets
tweets = api.request('search/tweets', {'q': '"%s"' % prompt})

fact = 'The %s (%s) %s' % (bird, scientific, re.sub(pronoun, '', prompt))

# look through tweets
for tweet in tweets:
    if not 'text' in tweet:
        continue
    text = tweet['text']
    if blacklist.check_blacklist(text):
        continue

    # lowercase just the prompt
    text = re.sub(prompt, prompt, text, flags=re.IGNORECASE)

    # put loose "sentences" on separate lines
    text = re.sub(r'([\.\?!\n\r]+)', r'\g<1>\n', text)
    # separate out usable string
    search = re.findall(
        r'^.*(%s(?!.*(?:\bhim\b|\bher\b|\bthem\b|\bme\b|@|http|…)).{10,200})' % prompt,
        text, re.M)
    try:
        text = search[0]
        text = re.sub(prompt, '', text)
    except IndexError:
        continue

    # end at end of sentence
    text = re.sub(r'([\.?!\n\r]).*$', r'\g<1>', text)
    if len(fact + text) < 280 and len(text) > 5:

        fact += text
        # avoid &amp; and similar
        fact = unescape(fact)

        print('tweet: twitter.com/%s/status/%d' % \
                (tweet['user']['screen_name'], tweet['id']))
        print('original text: %s' % tweet['text'])
        break

print('fact: %s' % fact)

# post that bird!
image_file = open(outpath, 'rb')
data = image_file.read()
r = api.request('statuses/update_with_media',
                {'status': fact}, {'media[]': data})
print(r.response)
