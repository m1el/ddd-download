import hashlib
import debrify as br
import bs4
import requests
import base64

session = requests.session()
def _parser(string):
  return bs4.BeautifulSoup(string, 'html5lib')

def get(url, drop_cache=False, parser=None):
  parser = parser or _parser
  cached = 'cache/' + hashlib.md5(url.encode()).hexdigest()
  text = None
  if not drop_cache:
    try:
      with open(cached, 'r', encoding='utf-8') as f:
        text = f.read()
    except Exception as e:
      pass
  if text is None:
    resp = session.get(url)
    text = resp.text
    with open(cached, 'w', encoding='utf-8') as f:
      f.write(text)

  return parser(text)

def get_post(postid):
  page = get(POST_URL(postid))
  post = page.select(POST_SEL(postid))
  if post:
    return (page, post[0].contents[1])
  else:
    return None, None

def split(ary, pred):
  ary = iter(ary)
  prev = next(ary)
  accum = [prev]
  for el in ary:
    if pred(prev, el):
      yield accum
      accum = [el]
    else:
      accum.append(el)
    prev = el
  yield accum

def is_el_gen(name):
  return lambda el: isinstance(el, bs4.Tag) and el.name == name

is_div = is_el_gen('div')
is_img = is_el_gen('img')
is_li = is_el_gen('li')

def wrap(doc, name, ary):
  ret = doc.new_tag(name)
  for el in ary:
    ret.append(el)
  return ret

def post_ps(doc, post):
  def strip(el):
    if not br.tag_strip(el):
      el = doc.new_tag('empty-line')
      el.can_be_empty_element = True
    return el

  for g in split(list(post.contents), lambda a, b: is_div(a) or is_div(b)):
    if is_div(g[0]):
      g = g[0]
      style = g.attrs.get('style', None)
      if style == 'text-align: center;':
        name = 'subtitle'
      elif style == 'text-align: right;':
        name = 'cite'
      else:
        name = 'section'
      if len(g.contents) > 1:
        els = map(strip, br.paragrify(doc, g))
        els = br.intersperse(els, '\n')
      else:
        els = [g.contents[0]]
      yield wrap(doc, name, list(els))
    else:
      els = map(strip, br.paragrify(doc, wrap(doc, post.name, g)))
      yield from br.intersperse(els, '\n')
    yield '\n'

def link_postid(link):
  split = link.attrs['href'].split('#post')
  if len(split) > 1:
    return (split[1], str(link.contents[0]))
  else:
    return None

THREAD = 'http://forums.nrvnqsr.com/showthread.php/2637-DDD'
POST_URL = (THREAD + '?p={0}').format
POST_SEL = '#post_message_{0}'.format
START = '900226'
IMG_MAP = {
    'http://i943.photobucket.com/albums/ad275/AITDerceto/ddd0105_s.jpg': 'ddd0105_s.png',
    'http://i943.photobucket.com/albums/ad275/AITDerceto/side_a024.jpg': 'side_a024.jpg',
    'http://i943.photobucket.com/albums/ad275/AITDerceto/dddp1.png': 'side_a026-a027.jpg',
    'http://i943.photobucket.com/albums/ad275/AITDerceto/dddp2.png': 'dddp2.png',
    'http://i943.photobucket.com/albums/ad275/AITDerceto/ddddd.png': 'side_b027.jpg',
    'http://i943.photobucket.com/albums/ad275/AITDerceto/Faust03_351.jpg': 'Faust03_351.jpg',
    'http://i943.photobucket.com/albums/ad275/AITDerceto/ddd0173_s.jpg': 'ddd0173_s.png',
    'http://i943.photobucket.com/albums/ad275/AITDerceto/side_b020.jpg': 'side_b020.jpg',
    'http://i943.photobucket.com/albums/ad275/AITDerceto/handL2.jpg': 'handL2.jpg',
    'http://i943.photobucket.com/albums/ad275/AITDerceto/ddd3.png': 'side_b053.jpg',
    'http://i943.photobucket.com/albums/ad275/AITDerceto/ddd4.png': '1062816_p0.jpg',
    'http://i943.photobucket.com/albums/ad275/AITDerceto/ddd5.png': 'ddd5.jpg',
    'http://i.imgur.com/YKCtchr.png': 'side_b089.jpg',
    'http://i.imgur.com/KbQUdSZ.jpg': 'KbQUdSZ.jpg',
    'http://i.imgur.com/Z4J2G6W.png': 'Z4J2G6W.png',
    'http://i.imgur.com/GtTPlF9.png': 'GtTPlF9.png',
    'http://i.imgur.com/aqD6kkB.png': 'aqD6kkB.png',
    'http://i.imgur.com/PJXrAtR.png': 'PJXrAtR.png', # ded link
    'http://i.imgur.com/qFuMOgW.png': 'qFuMOgW.png',
    'http://forums.nrvnqsr.com/attachment.php?attachmentid=11346&d=1446157668&thumb=1': 'DDD0007_s.png',
    }
IMG_TYPE = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    }

template = bs4.BeautifulSoup(open('template.fb2', 'rb'), 'xml')
body = template.select('body')[0]

doc, first = get_post(START)
idx = first.select('.alt2')[0]
posts = [link_postid(link)
         for link in idx.select('a[href]')
         if link_postid(link)]

for i, (p, t) in enumerate(posts):
  doc, post = get_post(p)
  if i == 0:
    while not is_img(post.contents[0]):
      post.contents[0].extract()

  expanding = post.select('div.alt2 div')
  if len(expanding):
    post = expanding[0]
  pars = list(post_ps(doc, post))
  title = wrap(template, 'title', [t])
  body.append(wrap(template, 'section', [title, '\n'] + pars))
  body.append('\n')

br.replace_text(body, r'^-- ', '— ')
br.replace_text(body, r'\x85', '…')
br.replace_text(body, r'\x97', '—')
br.fb2_tags(body)

for img in body.select('img'):
  src = img.attrs.get('src', None)
  if src in IMG_MAP:
    src = IMG_MAP[src]
    img.name = 'image'
    img.attrs['l:href'] = '#' + src
    del img.attrs['src']

    blob = template.new_tag('binary')
    blob.attrs['id'] = src
    blob.attrs['content-type'] = IMG_TYPE[src[-3:]]
    with open('img/' + src, 'rb') as f:
      blob.append(base64.b64encode(f.read()).decode())
    template.append(blob)

with open('ddd.fb2', 'w', encoding='utf-8') as out:
  out.write(str(template))
