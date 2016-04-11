import hashlib
import bs4
import re
Comment = bs4.Comment
Text = bs4.NavigableString
Tag = bs4.Tag

EMPTY_TAGS = set(['img'])

def split_by(arr, pred):
  accum = []
  for el in arr:
    if pred(el):
      yield accum
      accum = []
    else:
      accum.append(el)
  yield accum

def intersperse(sequence, val):
  for i, item in enumerate(sequence):
    if i != 0:
      yield val
    yield item

def chain(*iters):
  for it in iters:
    yield from it

def lift_br(doc, element):
  if type(element) == Text:
    return [str(element)]
  if element.name == 'br':
    return [None]

  def wrap(ary):
    ret = doc.new_tag(element.name)
    ret.attrs.update(element.attrs)
    for el in ary:
      ret.append(el)
    return ret

  children = (lift_br(doc, el) for el in element.contents)
  children = split_by(chain(*children), lambda x: x is None)
  return intersperse(map(wrap, children), None)

def paragrify(doc, element):
  element.attrs.clear()
  def rewrap(el):
    el.name = 'p'
    return el

  els = lift_br(doc, element)
  els = split_by(els, lambda x: x is None)
  return map(rewrap, chain(*els))

def tag_strip_side(element, right=False):
  tags = element.contents
  idx = -1 if right else 0
  while len(tags):
    tag = tags[idx]
    if type(tag) == Comment:
      tag.extract()
    elif type(tag) == Text:
      if right:
        text = str(tag).rstrip()
      else:
        text = str(tag).lstrip()
      if text:
        tag.replace_with(text)
        return True
      else:
        tag.extract()
    elif type(tag) == Tag:
      if tag.name in EMPTY_TAGS:
        return True
      if tag_strip_side(tag, right):
        return True
      else:
        tag.extract()
  return False

def walk(root, fn):
  fn(root)
  if type(root) == Tag:
    for el in root.contents:
      walk(el, fn)

def replace_text(el, rx, rep):
  for tag in el.contents:
    if type(tag) == Text:
      tag.replace_with(re.sub(rx, rep, tag))
    if type(tag) == Tag:
      replace_text(tag, rx, rep)

def tag_strip(el):
  return tag_strip_side(el, True) and tag_strip_side(el, False)

def fb2_tags(el):
  for tag in el.select('i'):
    tag.name = 'emphasis'
  for tag in el.select('b'):
    tag.name = 'strong'

