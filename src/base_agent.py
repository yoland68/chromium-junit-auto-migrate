#!/usr/bin/env python

import model
import parser

import abc

import json
import re
import logging
import argparse
import os
import collections
import sys

import codecs

_YEAR_PATTERN = re.compile(r'^(\/\/ Copyright) 2017')

_FLOAT_PATTERN = re.compile(r'^\d+?\.\d+f?$')

def _ReturnReplacement(pattern_string, replacement, string, flags=0, upper=False):
  pattern = re.compile(pattern_string, flags=flags)
  res = pattern.findall(string)
  if pattern_string == r'.*':
    res.remove('')
  if len(res) > 1:
    logging.warn('"%s" pattern is found more than once (%d) in "%s"' % (
      pattern_string, len(res), string if len(string) < 100
      else string[:100]+'...'))
  if upper:
    return pattern.sub(replacement, string, count=1).upper()
  return pattern.sub(replacement, string, count=1)


def _TraverseTree(tree):
  stack = [tree]
  element_list = []
  element_table = collections.defaultdict(list)

  while len(stack) != 0:
    current = stack.pop()
    if type(current) == list and len(current) > 0 and (any(
        isinstance(i, model.SourceElement) for i in current)):
      stack.extend(current)
    elif isinstance(current, model.SourceElement):
      element_list.append(current)
      element_table[type(current)].append(current)
      if getattr(current, '_fields'):
        for f in getattr(current, '_fields'):
          stack.append(getattr(current, f))
    # else:
#       logging.debug(
          # 'Current element in stack is neither SourceElement or list: '
          # + str(current) + ' : ' + str(type(current)) + ', gonna ignore')
  main_element_list, main_element_table = _GetMainListAndTable(element_list,
      element_table)
  return _SortListAndTable(
      element_list, element_table, main_element_list, main_element_table)


def _GetMainListAndTable(element_list, element_table):
  all_classes = element_table.get(model.ClassDeclaration, [])
  all_classes.extend(element_table.get(model.InterfaceDeclaration, []))
  if len(all_classes) == 1:
    return element_list, element_table
  else:
    main_element_list = []
    main_element_table = collections.defaultdict(list)
    for i in element_list:
      if len(
          [e for e in all_classes if i.lexpos >= e.lexpos
           and i.lexend <= e.lexend]) == 1:
        main_element_list.append(i)
        main_element_table[type(i)].append(i)
    return main_element_list, main_element_table


def _SortListAndTable(ls, tb, pls, ptb):
  sorted_element_list = sorted(ls, key=lambda x : x.lexpos)
  sorted_main_element_list = sorted(pls, key=lambda x: x.lexpos)
  sorted_element_table = {}
  sorted_main_element_table = {}
  for k, v in tb.iteritems():
    sorted_element_table[k] = sorted(v, key=lambda x: x.lexpos)
  for k, v in ptb.iteritems():
    sorted_main_element_table[k] = sorted(v, key=lambda x: x.lexpos)
  return (sorted_element_list, sorted_element_table,
          sorted_main_element_list, sorted_main_element_table)


def _GetMainClassAndSuperClassName(element_table):
  try:
    main_class = min(element_table[model.ClassDeclaration], key=lambda x:x.lexpos)
  except:
    import ipdb
    ipdb.set_trace()
  super_class_name = main_class.extends.name.value if main_class.extends is \
      not None else 'java.lang.Object'
  return main_class, super_class_name


class BaseAgent(object):
  """Basic agent for all java file, provide basic method"""

  def __init__(self, java_parser, filepath, logger=logging.getLogger(),
      agent=None, **kwargs):
    if agent != None and agent.filepath == filepath:
      assert isinstance(agent, BaseAgent)
      assert not agent._content_is_change
      self._tree = agent._tree
      self._filepath = agent._filepath
      self._content = agent.content
      self._main_element_list = agent._main_element_list
      self._main_element_table = agent._main_element_table
      self._element_list = agent._element_list
      self._element_table = agent._element_table
      self.main_class = agent.main_class
      self.super_class_name = agent.super_class_name

    else:
      self.Load(java_parser, filepath)

    self.logger = logger
    self.parser = java_parser
    self.kwargs = kwargs
    self._added_imports = []

  def actions(self):
    """Implement this to define the actions needed for a Java refactoring"""
    raise NotImplementedError("actions not implemented")

  def skip(self):
    """implement this to define whether to skip this test or not"""
    raise NotImplementedError("skip not implemented")

  @classmethod
  def ignore_files(cls):
    """return a list of ignored files"""
    raise NotImplementedError("ignore_files not implemented")

  @classmethod
  def filename_match(cls, whole_path):
    raise NotImplementedError("file_match not implemented")

  @staticmethod
  def _isPublicOrProtected(modifiers):
    return 'public' in modifiers or 'protected' in modifiers

  @staticmethod
  def _isStatic(modifiers):
    return 'static' in modifiers

  @property
  def content(self):
    return self._content

  @content.setter
  def content(self, value):
    self._content_is_change = True
    self._content = value

  @property
  def element_table(self):
    return self._element_table

  @property
  def element_list(self):
    return self._element_list

  @property
  def main_element_list(self):
    return self._main_element_list

  @property
  def main_element_table(self):
    return self._main_element_table

  @property
  def filepath(self):
    return self._filepath

  def actionOnX(self, classtype, condition=None, optional=False,
      main_table=False, action=None):
    if not condition:
      condition = lambda _: True
    element_table = (
        self.main_element_table if main_table else self.element_table)
    x_list = element_table.get(classtype)
    if x_list:
      narrow_list = [i for i in x_list if condition(i)]
      if action:
        for i in narrow_list:
          action(i)
      return narrow_list
    else:
      if optional:
        return []
      else:
        raise Exception('Did not find any this type of element in code')


  def actionOnMethodInvocation(self, condition=None, optional=False,
        main_table=False, action=None):
    return self.actionOnX(
        model.MethodInvocation, condition=condition, optional=optional,
        main_table=main_table, action=action)

  def actionOnMethodDeclaration(self, condition=None, optional=False,
        main_table=False, action=None):
    return self.actionOnX(
        model.MethodDeclaration, condition=condition, optional=optional,
        main_table=main_table, action=action)

  def Load(self, java_parser, filepath):
    with open(filepath) as f:
      self._tree = java_parser.parse_file(f)
    self._filepath = filepath #the filepath to the javafile
    with codecs.open(filepath, encoding='utf-8', mode='r') as f:
      self._content = f.read() #content string of original java file
    self._content_is_change = False
    self._element_list, self._element_table, self._main_element_list, \
        self._main_element_table = _TraverseTree(self._tree)
    assert len(self._element_list) > 0, "%s file does not have content" % filepath

    self._content_is_change = False

    #table that maps lexpos to the offset amount
    self.offset_table = collections.defaultdict(int)
    self.offset_table[0] = -2

    self.main_class, self.super_class_name = _GetMainClassAndSuperClassName(
        self._element_table)

  def Save(self):
    output_file_path = self._filepath
    if self.kwargs.get('save_as_new', False):
      output_file_path = output_file_path + '.new'
    with codecs.open(output_file_path, encoding='utf-8', mode='w') as f:
      f.write(self.content)
    return output_file_path

  def SaveAndReload(self):
    output_file_path = self.Save()
    self.Load(self.parser, output_file_path)

  def _locToNextElement(self, loc):
    for i in self.element_list:
      if self._lexposToLoc(i.lexpos) > loc:
        return i

  def _lexposToLoc(self, lex):
    offset = 0
    for i,j in self.offset_table.items():
      if i <= lex:
        offset += j
    return offset+lex

  def _removeElement(self, e):
    return self._replaceString(r'.*', '', element=e, flags=re.DOTALL)

  def _isDeclaredLocally(self, method):
    for declaration in self.main_element_table.get(model.MethodDeclaration, []):
      if declaration.name == method.name:
        return True

  def _argumentIsFloatOrDouble(self, element):
    assert isinstance(element, model.MethodInvocation)
    for arg in element.arguments:
      if isinstance(arg, model.Literal):
        return _FLOAT_PATTERN.match(arg.value) is not None
      elif isinstance(arg, model.Multiplicative):
        if (_FLOAT_PATTERN.match(arg.lhs.value) or
            _FLOAT_PATTERN.match(arg.rhs.value)):
          return True
      elif isinstance(arg, model.Name):
        possible_vars = [
            i for i in self.element_table.get(model.VariableDeclaration, []) if
            i.variable_declarators[0].variable.name == arg.value and
            i.lineno < arg.lineno]
        if len(possible_vars) == 0:
          return False
        current_var = possible_vars[0]
        for i in possible_vars:
          if arg.lineno - i.lineno < arg.lineno - current_var.lineno:
            current_var = i
        if isinstance(current_var.type, model.Type):
          if current_var.type.name.value in ['Double', 'Float']:
            return True
        else:
          if current_var.type in ['double', 'float', 'Double', 'Float']:
            return True
          else:
            return False
      elif isinstance(arg, model.MethodInvocation):
        if any(i for i in self.element_table[model.MethodDeclaration] if
               i.name == arg.name and i.return_type in
               ['double', 'float', 'Double', 'Float']):
          return True
    return False

  def _isInherited(self, method):
    assert type(method) == model.MethodInvocation
    if method.target is not None:
      return False
    if self._isImportedStaticMethod(method):
      return False
    for declaration in self.main_element_table[model.MethodDeclaration]:
      if declaration.name == method.name:
        return False
    return True

  def _insertInBetween(self, insertion, start, end):
    self.content = (
      self.content[:start] + insertion + self.content[end:])

  def _insertBelow(self, element, partial_insertion, auto_indentation=True):
    index = self._lexposToLoc(element.lexpos)
    indentation = 0
    while self.content[index] != '\n':
      if self.content[index] == ' ':
        indentation += 1
      elif self.content[index] != ' ':
        indentation = 0
      index -= 1
    index = self._lexposToLoc(element.lexpos)
    while self.content[index] != '\n':
      index += 1
    if auto_indentation:
      insertion = ' ' * indentation + partial_insertion + '\n'
    else:
      insertion = partial_insertion + '\n'
    self._insertInBetween(insertion, index+1, index+1)
    next_element = self._findNextElementIndex(element)
    while self._lexposToLoc(next_element.lexpos) <= index:
      next_element = self._findNextElementIndex(next_element)
    self.offset_table[next_element.lexpos] += len(insertion)

  def _insertAbove(self, element, partial_insertion, auto_indentation=True):
    index = self._lexposToLoc(element.lexpos)
    indentation = 0
    while self.content[index] != '\n':
      if self.content[index] == ' ':
        indentation += 1
      elif self.content[index] != ' ':
        indentation = 0
      index -= 1
    if auto_indentation:
      insertion = ' ' * indentation + partial_insertion + '\n'
    else:
      insertion = partial_insertion + '\n'
    self._insertInBetween(insertion, index+1, index+1)
    self.offset_table[element.lexpos] += len(insertion)

  def _insertInfront(self, element, insertion):
    index = self._lexposToLoc(element.lexpos)
    self._insertInBetween(insertion, index, index)
    self.offset_table[element.lexpos] += len(insertion)

  def _replaceString(self, pattern, replacement, element=None, optional=True,
                     start=None, end=None, flags=0, verbose=False, upper=False):
    if start is None:
      start = self._lexposToLoc(element.lexpos)
    if end is None:
      end = self._lexposToLoc(element.lexend)
    content_string = self.content[start:end+1]
    search_res = re.search(pattern, content_string, flags=flags)
    if optional and search_res is None:
      return
    elif not optional and search_res is None:
      raise Exception('Element not found')
    change_loc = start+search_res.start()
    content_replacement = _ReturnReplacement(
        pattern, replacement, content_string, flags=flags, upper=upper)
    next_element = self._locToNextElement(change_loc)
    self.content = (
        self.content[:start] + content_replacement + self.content[end+1:])
    if verbose:
      logging.debug("Before: " + content_string)
      logging.debug("After : " + content_replacement)

    if next_element is not None:
      self.offset_table[next_element.lexpos] = (
          len(content_replacement) - len(content_string))
    return content_string

  def _findNextElementIndex(self, element):
    for i, j in enumerate(self.element_list):
      if j == element:
        if i == len(self.element_list) - 1:
          #If it's the last element, return a sentinel
          return model.SourceElement(
              lineno = j.lineno+1, lexpos = len(self.content)-1)
        else:
          return self.element_list[i+1]

  def _findNextParallelElementIndex(self, element):
    for i, j in enumerate(self.element_table[type(element)]):
      if j == element:
        if i == len(self.element_table[type(element)]) - 1:
          #If it's the last element, return a sentinel
          return model.SourceElement(
              lineno = j.lineno+1, lexpos = len(self.content)-1)
        else:
          return self.element_table[type(element)][i+1]
    raise Exception('Element not found')

  def _addImport(self, package):
    if package not in self._added_imports:
      self._added_imports.append(package)
      import_string = 'import ' +  package + ';'
      if len(self.element_table[model.ImportDeclaration]) == 0:
        self._insertBelow(
            self.element_table[model.PackageDeclaration][0],
            import_string)
      else:
        self._insertBelow(
            self.element_table[model.ImportDeclaration][-1],
            import_string)

  def _isImportedType(self, type_element):
    assert isinstance(type_element, model.InstanceCreation)
    for i in self.element_table[model.ImportDeclaration]:
      if i.name.value.split('.')[-1] == type_element.type.name.value:
        return True
    return False

  def _isImportedStaticMethod(self, method):
    assert isinstance(method, model.MethodInvocation)
    for i in self.element_table[model.ImportDeclaration]:
      if i.name.value.split('.')[-1] == method.name:
        return True
    return False

  def _removeImport(self, import_name):
    start = self._lexposToLoc(
        self.element_table[model.ImportDeclaration][0].lexpos)
    end = self._lexposToLoc(
        self.element_table[model.ImportDeclaration][-1].lexend)
    self._replaceString(r'import.*%s; *\n' % import_name, '', start=start,
                        end=end)

  def replaceYear(self):
    """Change copyright year to 2017"""
    self.content = _YEAR_PATTERN.sub(r'\1 2015', self.content, count=1)
