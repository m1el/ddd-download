import hashlib
import debrify as br
import bs4
import requests

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

template = bs4.BeautifulSoup(open('template.fb2', 'rb'), 'xml')
body = template.select('body')[0]

doc, first = get_post(START)
idx = first.select('.alt2')[0]
posts = [link_postid(link)
         for link in idx.select('a[href]')
         if link_postid(link)]
while not is_img(first.contents[0]):
  first.contents[0].extract()
pars = list(post_ps(doc, first))
title = wrap(template, 'title', ['HandS.(R)'])
body.append(wrap(template, 'section', [title] + pars))

for p, t in (p for p in posts if p[0] != START):
  doc, post = get_post(p)
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
with open('ddd.fb2', 'w', encoding='utf-8') as out:
  out.write(str(template))
