#!/usr/bin/env python

import model
import parser
import base_agent

import json
import re
import os
import collections
import codecs
import logging

_YEAR_PATTERN = re.compile(r'^(\/\/ Copyright) 2017')

_FLOAT_PATTERN = re.compile(r'^\d+?\.\d+f?$')

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

_IGNORED_APIS = {
    'getClass', 'sendKeys', 'runTestOnUiThread', 'getInstrumentation',
    'setndRepeatedKeys', 'injectInstrumentation'}

_TEST_RULE_METHODS = {'run', 'apply', 'evaluate'}

def AnalyzeMapping(java_parser, mapping):
  stack = []
  for key, info in mapping.items():
    f = base_agent.BaseAgent(java_parser, info['location'])
    api_list = [m.name for m in f.main_element_table[model.MethodDeclaration]
                if f._isPublicOrProtected(m.modifiers) and
                m.name not in _TEST_RULE_METHODS]
    local_accessible_interface = [
        m.name for m in f.main_element_table.get(model.InterfaceDeclaration, [])
        if f._isPublicOrProtected(m.modifiers)]
    local_accessible_annotation = [
        m.name for m in f.main_element_table.get(
            model.AnnotationDeclaration, [])
        if f._isPublicOrProtected(m.modifiers)]
    local_accessible_class = [
        m.name for m in f.element_table.get(model.ClassDeclaration, [])
        if f._isPublicOrProtected(m.modifiers) and m.name != f.main_class.name]
    info.update({
      'api': list(set(api_list)),
      'types': local_accessible_class
          +local_accessible_interface+local_accessible_annotation})
    if f.super_class_name not in ['java.lang.Object', 'ActivityTestRule']:
      info.update({'parent': f.super_class_name})
    else:
      stack.append((key, info['rule']))

  #Inheritance
  while len(stack) != 0:
    el = stack.pop()
    for k, v in mapping.items():
      if v.get('parent') == el[1]:
        v['api'].extend(mapping[el[0]]['api'])
        v['special_method_change'].update(
            mapping[el[0]]['special_method_change'])
        stack.append(k)
  return mapping


class TestConvertAgent(base_agent.BaseAgent):
  def __init__(self, java_parser, filepath, logger=logging.getLogger,
               agent=None, **kwargs):
    super(TestConvertAgent, self).__init__(java_parser, filepath, logger, agent,
                                           **kwargs)
    if type(agent) == type(self):
      self._api_mapping = agent.api_mapping
    else:
      self._api_mapping = AnalyzeMapping(self.parser, self.raw_api_mapping())

  @property
  def api_mapping(self):
    return self._api_mapping

  @property
  def rule_dict(self):
    return self.api_mapping.get(self.super_class_name, {})

  @staticmethod
  def raw_api_mapping():
    """implement this class method to return mapping from base class to rules"""
    raise NotImplementedError("raw_api_mapping not implemented")

  @classmethod
  def filename_match(cls, file_whole_path):
    if (file_whole_path.endswith('Test.java') and file_whole_path not in
        cls.ignore_files()):
      return True
    else:
      return False

  def _insertActivityTestRule(self, var_type, instantiation, var):
    element = self.main_class.body[0]
    self._insertAbove(element, '\n    @Rule', auto_indentation=False)
    self._insertAbove(
        element,
        '    public %s %s = new %s;' % (
            var_type, var, instantiation),
        auto_indentation=False)
    self._insertAbove(element, '\n', auto_indentation=False);
    self._addImport('org.junit.Rule')
    self._addImport('org.chromium.chrome.browser.ChromeActivity')


  def isJUnit4(self):
    """Check if the test class is already JUnit4 by checking its super class"""
    return self.super_class_name == 'java.lang.Object'

  def changeRunTestOnUiThread(self):
    for m in self.element_table[model.MethodInvocation]:
      if m.name == 'runTestOnUiThread' and not self._isDeclaredLocally(m):
        self._replaceString(
        'runTestOnUiThread',
        'InstrumentationRegistry.getInstrumentation().runOnMainSync',
        element=m)

  def changeApis(self):
    activity_rule = self.rule_dict['var']
    for m in self.element_table.get(model.MethodInvocation, []):
      if self._isInherited(m) and m.target is None:
        if self.api_mapping and self.api_mapping.get(self.super_class_name):
          if m.name in _ASSERTION_METHOD_SET or m.name in _IGNORED_APIS:
            continue
          elif (m.name in self.api_mapping[self.super_class_name]['api'] or
              m.name in _SPECIAL_INSTRUMENTATION_TEST_CASE_APIS):
            self._insertInfront(m, activity_rule+'.')
          elif m.name in self.api_mapping[self.super_class_name].get(
              'special_method_change',{}).keys():
            self._replaceString(
                m.name,
                activity_rule+'.'+self.api_mapping[self.super_class_name][
                    'special_method_change'][m.name],
                element=m,
                optional=False)

          else:
            self.logger.info('Can NOT handle this method call: %s' %
                          m.name)

  def changeSetUpTearDown(self):
    methods = dict(
        (m.name, m) for m in self.element_table[model.MethodDeclaration]
        if m.name in ['setUp', 'tearDown'])
    if methods.get('setUp'):
      m = methods.get('setUp')
      self._replaceString('protected', 'public', element=m, optional=True)
      self._insertAbove(m, '@Before')
      self._addImport('org.junit.Before')
      self._replaceString(r' *@Override\n', '', element=m, optional=True)
      self._replaceString(
          r' *super.setUp\(.*\); *\n', '', element=m, optional=True)
    if methods.get('tearDown'):
      m = methods.get('tearDown')
      self._replaceString('protected', 'public', element=m, optional=True)
      self._insertAbove(m, '@After')
      self._addImport('org.junit.After')
      self._replaceString(r' *@Override\n', '', element=m, optional=True)
      self._replaceString(
          r' *super.tearDown\(.*\) *;\n', '', element=m, optional=True)

  def changeAssertions(self):
    for m in self.element_table[model.MethodInvocation]:
      if m.name in _ASSERTION_METHOD_SET and m.target is None:
        if (m.name == 'assertEquals' and len(m.arguments) == 2 and
            self._argumentIsFloatOrDouble(m)):
          self._addImport('org.junit.Assert')
          self._replaceString(
              r'assertEquals\((.*)\)', r'Assert.assertEquals(\1, 0)', element=m,
              optional=False, flags=re.DOTALL, verbose=True)
        else:
          self._addImport('org.junit.Assert')
          self._removeImport('junit.framework.Assert')
          self._insertInfront(m, 'Assert.')

  def replaceInstrumentationApis(self):
    for m in self.element_table[model.MethodInvocation]:
      if m.name == 'getInstrumentation' and self._isInherited(m):
        self._insertInfront(m, 'InstrumentationRegistry.')
        self._addImport('android.support.test.InstrumentationRegistry')
      if m.name == 'getContext' and m.target is None:
        self._insertInfront(m, 'InstrumentationRegistry.')
        self._addImport('android.support.test.InstrumentationRegistry')

  def addClassRunner(
      self, runner_name='BaseJUnit4ClassRunner',
      runner_package='org.chromium.base.test.BaseJUnit4ClassRunner'):
    self._addImport('org.junit.runner.RunWith')
    self._addImport(runner_package)
    self._insertAbove(self.main_class, '@RunWith(%s.class)' % runner_name)

  def removeExtends(self):
    self._removeImport(self.super_class_name)
    if len(self.rule_dict) != 0:
      self._addImport(self.rule_dict['package'] + '.' + self.rule_dict['rule'])
    self._replaceString(r'extends .*? {', '{',
                        element=self.main_class, flags=re.DOTALL)


  def removeConstructor(self):
    if len(self.main_element_table[model.ConstructorDeclaration]) != 0:
      self._replaceString('.*', '',
          element=self.main_element_table[model.ConstructorDeclaration][0],
          flags=re.DOTALL)

  def changeMinSdkAnnotation(self):
    for a in self.main_element_table.get(model.Annotation):
      if a.name == 'MinAndroidSdkLevel':
        self._replaceString(r'@MinAndroidSdkLevel\((.*)\)', r'@SdkSuppress\1',
            element=a)
        self._removeImport('org.chromium.base.test.util.MinAndroidSdkLevel')
        self._addImport('android.support.test.filters.SdkSuppress')

  def addTestAnnotation(self):
    for m in self.main_element_table.get(model.MethodDeclaration, []):
      if m.name.startswith('test'):
        self._insertAbove(m, '@Test')
        self._addImport('org.junit.Test')

  def insertActivityTestRuleTest(self):
    if self.api_mapping and len(self.rule_dict) != 0:
      self._insertActivityTestRule(
          self.rule_dict['rule_var'], self.rule_dict['instan'],
          self.rule_dict['var'])

  def importTypes(self):
    for _, info in self.api_mapping.iteritems():
      for i in info['types']:
        for x in self.element_list:
          if isinstance(x, model.Annotation) and getattr(x.name, "value",
              None) == i:
            self._addImport(
                '.'.join([info['package'], info['rule'], i]))
          if isinstance(x, model.Type):
            if type(x.name) == str and x.name == i:
              self._addImport(
                  '.'.join([info['package'], info['rule'], i]))
            elif type(getattr(
                x.name, 'value', None)) == str and x.name.value == i:
              self._addImport(
                  '.'.join([info['package'], info['rule'], i]))
