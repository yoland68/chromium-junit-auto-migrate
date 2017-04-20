import parser as ply
import model as model

import collections
import logging

def traverseTreeToTable(tree):
  source_element_table = collections.defaultdict(list)
  source_element_list = []

  stack = [tree]
  while len(stack) != 0:
    current = stack.pop()
    if type(current) == list and len(current) > 0 and (
          any(isinstance(i, model.SourceElement) for i in current)):
      stack.extend(current)
    elif isinstance(current, model.SourceElement):
      source_element_table[type(current)].append(current)
      source_element_list.append(current)
      if getattr(current, '_fields'):
        for f in getattr(current, '_fields'):
          stack.append(getattr(current, f))
    else:
      logging.debug(
          'Current element in stack is neither SourceElement or list: '
          + str(current) + ' : ' + str(type(current)) + ', gonna ignore')
  return _SortListAndTable(source_element_list, source_element_table)

def _SortListAndTable(ls, tb):
  sorted_element_list = sorted(ls, key=lambda x : x.lexpos)
  sorted_element_table = {}
  for k, v in tb.iteritems():
    sorted_element_table[k] = sorted(v, key=lambda x: x.lexpos)
  return sorted_element_list, sorted_element_table

def main():
  logger = logging.getLogger()
  logger.setLevel(logging.ERROR)
  parser = ply.Parser(errorlog=logger)
  tree = parser.parse_file(
      file('chrome/android/javatests/src/org/chromium/chrome/browser/toolbar/BrandColorTest.java'))
  ls, tb = traverseTreeToTable(tree)
  import ipdb
  ipdb.set_trace()

main()
