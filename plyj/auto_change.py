#!/usr/bin/env python

import model
import parser

import json
import re
import logging
import argparse
import os
import collections
import sys

import codecs

_YEAR_PATTERN = re.compile(r'^(\/\/ Copyright) 20\d\d')

_ASSERTION_METHOD_SET = {
    'assertEquals',
    'assertFalse',
    'assertNotNull',
    'assertNotSame',
    'assertNull',
    'assertSame',
    'assertTrue',
    'fail'}

_SPECIAL_SUPER_CLASS = {
    'BaseActivityInstrumentationTestCase',
    'ActivityInstrumentationTestCase2',
    'ActivityTestCase',
    'InstrumentationTestCase',
    'TestCase'
}


_SPECIAL_INSTRUMENTATION_TEST_CASE_APIS = {
    'getActivity',
}

_TEST_RULE_METHODS = {'run', 'apply', 'evaluate'}

class ElementWrapper(object):
  def __init__(self, element, parent):
    assert isinstance(element, model.SourceElement)
    self.element = element
    self.parent = parent

def _ReturnReplacement(pattern_string, replacement, string, flags=0):
  pattern = re.compile(pattern_string, flags=flags)
  res = pattern.findall(string)
  if len(res) > 1:
    logging.warning('"%s" pattern is found more than once (%d) in "%s"' % (
                    pattern_string, len(res), string))
  return pattern.sub(replacement, string, count=1)

def _SetIfNone(element, func):
  if element is None:
    element = func()
  return element

def TraverseTree(tree):
  stack = [tree]
  element_list = []
  element_table = collections.defaultdict(list)
  main_element_list= []
  main_element_table = collections.defaultdict(list)

  parent_stack = [tree.type_declarations[0]]
  parent = parent_stack[-1]
  while len(stack) != 0:
    current = stack.pop()
    if isinstance(current, model.ClassDeclaration) and current not in parent_stack:
      parent_stack.append(current)
    if type(current) == list and len(current) > 0 and (
          any(isinstance(i, model.SourceElement) for i in current)):
      stack.extend(current)
    elif isinstance(current, model.SourceElement):
      if current.lexpos > parent.lexend:
        parent_stack.pop()
        parent = parent_stack[-1]
      element_list.append(current)
      element_table[type(current)].append(current)
      if len(parent_stack) == 1:
        main_element_list.append(current)
        main_element_table[type(current)].append(current)
      if getattr(current, '_fields'):
        for f in getattr(current, '_fields'):
          stack.append(getattr(current, f))
    else:
      logging.debug(
          'Current element in stack is neither SourceElement or list: '
          + str(current) + ' : ' + str(type(current)) + ', gonna ignore')
  return _SortListAndTable(
      element_list, element_table, main_element_list, main_element_table)

def _SortListAndTable(ls, tb, pls, ptb):
  sorted_element_list = sorted(ls, key=lambda x : x.lexpos)
  sorted_main_element_list = sorted(pls, key=lambda x: x.lexpos)
  sorted_element_table = {}
  sorted_main_element_table = {}
  #ipdb.set_trace()
  for k, v in tb.iteritems():
    sorted_element_table[k] = sorted(v, key=lambda x: x.lexpos)
  for k, v in ptb.iteritems():
    sorted_main_element_table[k] = sorted(v, key=lambda x: x.lexpos)
  return (sorted_element_list, sorted_element_table,
          sorted_main_element_list, sorted_main_element_table)

class JavaFileTree(object):
  def __init__(self, tree, filepath, api_mapping, content=None):
    self._tree = tree
    self._filepath = filepath #the filepath to the javafile
    if filepath:
      with codecs.open(filepath, encoding='utf-8', mode='r') as f:
        self._content = f.read() #content string of original java file
    else:
      self._content = content
    self._element_list, self._element_table, self._main_element_list, \
        self._main_element_table = TraverseTree(self._tree)
    assert len(self._element_list) > 0

    self.mapping = api_mapping

    self.super_class_name = 'java.lang.Object'
    if len(self._element_table.get(model.ClassDeclaration, [])) > 0:
      self.main_class = min(
          self._element_table[model.ClassDeclaration], key=lambda x:x.lexpos)
      if self.main_class.extends is not None:
        self.super_class_name = self.main_class.extends.name.value

    self.added_imports = []

    #table that maps lexpos to the offset amount
    self.offset_table = collections.defaultdict(int)
    self.offset_table[0] = -2

    self.extends = None

  @property
  def content(self):
    return self._content

  @content.setter
  def content(self, value):
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

  def _isDeclaredLocally(self, method):
    for declaration in self.main_element_table.get(model.MethodDeclaration, []):
      if declaration.name == method.name:
        return True

  def _isInherited(self, method):
    assert type(method) == model.MethodInvocation
    if method.target is not None:
      return False
    if self._isImportedStaticMethod(method):
      return False
    for declaration in self.element_table[model.MethodDeclaration]:
      if declaration.name == method.name:
        return False
    return True

  def _traverseTree(self):
    stack = [self._tree]
    while len(stack) != 0:
      current = stack.pop()
      if type(current) == list and len(current) > 0 and (
            any(isinstance(i, model.SourceElement) for i in current)):
        stack.extend(current)
      elif isinstance(current, model.SourceElement):
        self._element_table[type(current)].append(current)
        self._element_list.append(current)
        if getattr(current, '_fields'):
          for f in getattr(current, '_fields'):
            stack.append(getattr(current, f))
      else:
        logging.debug(
            'Current element in stack is neither SourceElement or list: '
            + str(current) + ' : ' + str(type(current)) + ', gonna ignore')

  def _sortData(self):
    self._element_list = sorted(
        self._element_list, key=lambda x : x.lexpos)
    for k, v in self._element_table.iteritems():
      self._element_table[k] = sorted(v, key=lambda x: x.lexpos)

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

  def _insertAbove(self, element, partial_insertion):
    index = self._lexposToLoc(element.lexpos)
    indentation = 0
    while self.content[index] != '\n':
      if self.content[index] == ' ':
        indentation += 1
      elif self.content[index] != ' ':
        indentation = 0
      index -= 1
    insertion = ' ' * indentation + partial_insertion + '\n'
    self._insertInBetween(insertion, index+1, index+1)
    self.offset_table[element.lexpos] += len(insertion)

  def _insertInfront(self, element, insertion):
    index = self._lexposToLoc(element.lexpos)
    self._insertInBetween(insertion, index, index)
    self.offset_table[element.lexpos] += len(insertion)

  def _replaceString(self, pattern, replacement, element=None, optional=True,
                     start=None, end=None, flags=0):
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
        pattern, replacement, content_string, flags=flags)
    next_element = self._locToNextElement(change_loc)
    self.content = (
        self.content[:start] + content_replacement + self._content[end+1:])
    if next_element is not None:
      self.offset_table[next_element.lexpos] = (
          len(content_replacement) - len(content_string))

  def _findNextElementIndex(self, element):
    for i, j in enumerate(self.element_list):
      if j == element:
        if i == len(self.element_list) - 1:
          #If it's the last element, return a sentinel
          return model.SourceElement(
              lineno = j.lineno+1, lexpos = len(self.content)-1)
        else:
          return self.element_list[i+1]

  def _insertActivityTestRule(
      self, var_type, instantiation, var='mActivityTestRule'):
    if self.main_class.extends is not None:
      element = self.main_class.extends
    else:
      element = self.main_class
    self._insertBelow(
        element,
        '    public %s %s = new %s;' % (
            var_type, var, instantiation),
        auto_indentation=False)
    self._insertBelow(element, '\n    @Rule', auto_indentation=False)
    self._addImport('org.junit.Rule')

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
    if package not in self.added_imports:
      self.added_imports.append(package)
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

  def _replaceImport(self, import_name, rule_type):
    start = self._lexposToLoc(
        self.element_table[model.ImportDeclaration][0].lexpos)
    end = self._lexposToLoc(
        self.element_table[model.ImportDeclaration][-1].lexend)
    self._replaceString(r'(import.*)%s; *$' % import_name,
                        r'\1%s;' % rule_type,
                        start=start, end=end)

  def changeRunTestOnUiThread(self, rule_var_name='mActivityTestRule'):
    for m in self.element_table[model.MethodDeclaration]:
      if m.name == 'runTestOnUiThread' and not self._isDeclaredLocally(m):
        self._replaceString(
            'runTestOnUiThread', rule_var_name+'.'+'runOnUiThread', element=m)

  def isJUnit4(self):
    """Check if the test class is already JUnit4 by checking its super class"""
    return self.super_class_name == 'java.lang.Object'

  def replaceYear(self):
    """Change copyright year to 2017"""
    self._content = _YEAR_PATTERN.sub(r'\1 2017', self._content, count=1)

  def changeSetUp(self):
    for m in self.element_table[model.MethodDeclaration]:
      if m.name == 'setUp':
        self._replaceString('protected', 'public', element=m, optional=True)
        self._insertAbove(m, '@Before')
        self._addImport('org.junit.Before')
        self._replaceString(r' *@Override', '', element=m, optional=True)
        self._replaceString(
            r' *super.setUp\(.*\); *\n', '', element=m, optional=True)
      if m.name == 'tearDown':
        self._replaceString('protected', 'public', element=m, optional=True)
        self._insertAbove(m, '@After')
        self._addImport('org.junit.After')
        self._replaceString(r' *@Override', '', element=m, optional=True)
        self._replaceString(
            r' *super.tearDown\(.*\) *;\n', '', element=m, optional=True)

  def changeAssertions(self):
    for m in self.element_table[model.MethodInvocation]:
      if m.name in _ASSERTION_METHOD_SET:
        self._addImport('org.junit.Assert')
        self._insertInfront(m, 'Assert.')

  def replaceInstrumentationApis(self):
    for m in self.element_table[model.MethodInvocation]:
      if m.name == 'getInstrumentation' and self._isInherited(m):
        self._insertInfront(m, 'InstrumentationRegistry.')
        self._addImport('android.support.test.InstrumentationRegistry')

  def addClassRunner(
      self, runner_name='BaseJUnit4ClassRunner',
      runner_package='org.chromium.base.test.BaseJUnit4ClassRunner'):
    self._addImport('org.junit.runner.RunWith')
    self._addImport(runner_package)
    self._insertAbove(self.main_class, '@RunWith(%s.class)' % runner_name)

  def removeExtends(self):
    self._replaceImport(
        self.super_class_name, self.mapping.get(self.super_class_name)['rule'])
    self._replaceString(r'extends .*? {', '{',
                        element=self.main_class, flags=re.DOTALL)

  def addTestAnnotation(self):
    for m in self.main_element_table[model.MethodDeclaration]:
      if m.name.startswith('test'):
        self._insertAbove(m, '@Test')
        self._addImport('org.junit.Test')

  def insertActivityTestRuleTest(self):
    if self.mapping and self.mapping.get(self.super_class_name):
      self._insertActivityTestRule(
          self.mapping.get(self.super_class_name)['rule_var'],
          self.mapping.get(self.super_class_name)['instan'])

  def changeApis(self, activity_rule='mActivityTestRule'):
    for m in self.main_element_table[model.MethodInvocation]:
      if self._isInherited(m):
        if self.mapping and self.mapping.get(self.super_class_name):
          if (m.name in self.mapping[self.super_class_name]['api'] or
              m.name in _SPECIAL_INSTRUMENTATION_TEST_CASE_APIS):
            self._insertInfront(m, activity_rule+'.')
          elif m.name in self.mapping[self.super_class_name]['special_method_change'].keys():
            self._replaceString(
                m.name,
                self.mapping[self.super_class_name]['special_method_change'][m.name],
                element=m,
                optional=False)

          elif m.name in _ASSERTION_METHOD_SET:
            continue
          else:
            logging.warning('I do not know how to handle this method call: %s' %
                          m.name)

def _isPublicOrProtected(modifiers):
  return 'public' in modifiers or 'protected' in modifiers

def AnalyzeMapping(java_parser, mapping):
  for _, info in mapping.iteritems():
    file_tree = java_parser.parse_file(file(info['location']))
    f = JavaFileTree(file_tree, info['location'], mapping)
    api_list = [m.name for m in f.main_element_table[model.MethodDeclaration]
                if _isPublicOrProtected(m.modifiers) and
                m.name not in _TEST_RULE_METHODS]
    local_accessible_interface = [
        m.name for m in f.main_element_table.get(model.InterfaceDeclaration, [])
        if _isPublicOrProtected(m.modifiers)]
    local_accessible_class = [
        m.name for m in f.main_element_table.get(model.ClassDeclaration, [])
        if _isPublicOrProtected(m.modifiers)]
    info.update({
      'api': list(set(api_list)),
      'types': local_accessible_class+local_accessible_interface,
      'parent': f.super_class_name if f.super_class_name not in [
          'java.lang.Object', 'ActivityTestRule'] else None})
  return mapping

def ConvertDirectory(directory, java_parser, mapping, save_as_new=False):
  for (dirpath, _, filenames) in os.walk(directory):
    for filename in filenames:
      if filename.endswith('Test.java'):
        ConvertFile(
            os.path.join(dirpath, filename), java_parser, mapping, save_as_new)

def ConvertFile(filepath, java_parser, api_mapping, save_as_new=False):
  file_tree = java_parser.parse_file(file(filepath))
  f = JavaFileTree(file_tree, filepath, api_mapping)
  logging.info('current file is %s' % filepath)
  if f.isJUnit4():
    logging.info('%s is already junit 4' % filepath)
  else:
    f.replaceYear()
    f.removeExtends()
    f.changeSetUp()
    f.changeAssertions()
    f.replaceInstrumentationApis()
    f.addClassRunner()
    f.addTestAnnotation()
    f.insertActivityTestRuleTest()
    f.changeApis()
    if save_as_new:
      filepath += '.new'
    with codecs.open(filepath, encoding='utf-8', mode='w') as f_new:
      f_new.write(f.content)


def main():
  #TODO: add argparse
  argument_parser = argparse.ArgumentParser()
  argument_parser.add_argument('-f', '--java-file', help='Java file')
  argument_parser.add_argument('-n', '--save-as-new', default=False,
                               action='store_true', help='Save as a new file')
  argument_parser.add_argument('-d', '--directory',
                               help='Directory where all java file lives')
  argument_parser.add_argument(
      '-m', '--mapping-file', dest='mapping_file', required=True,
      help='json file that maps all the TestBase to TestRule info')
  arguments = argument_parser.parse_args(sys.argv[1:])

  if arguments.java_file and arguments.directory:
    raise Exception(
        'Can not specify --jave-file and --directory at the same time')
  logger = logging.getLogger('parser_logger')
  logger.setLevel(logging.ERROR)
  java_parser = parser.Parser(logger)
  with open(os.path.abspath(arguments.mapping_file), 'r') as f:
    mapping = json.loads(f.read())
    mapping = AnalyzeMapping(java_parser, mapping)
  if arguments.java_file:
    ConvertFile(arguments.java_file, java_parser, mapping,
                save_as_new=arguments.save_as_new)
  else:
    ConvertDirectory(arguments.directory, java_parser, mapping,
                     save_as_new=arguments.save_as_new)

  # ConvertFile('/usr/local/google/home/yolandyan/Code/clankium/src/content/shell/android/javatests/src/org/chromium/content_shell_apk/ContentShellShellManagementTest.java.old', java_parser, api_mapping)

if __name__ == '__main__':
  main()

