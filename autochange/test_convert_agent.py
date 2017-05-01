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

_INSTRUMENTATION_REGISTRY_METHODS = {
    'getInstrumentation', 'getContext', 'getTargetContext'
}

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

  @staticmethod
  def class_runner():
    """return a tuple of the name of the class runner and it's package"""
    raise NotImplementedError("class_runner() not implemented")

  @property
  def rule_var(self):
    return self.rule_dict['var']

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


  def isJUnit4(self):
    """Check if the test class is already JUnit4 by checking its super class"""
    return self.super_class_name == 'java.lang.Object'

  def changeRunTestOnUiThread(self):
    self.actionOnMethodInvocation(
        condition=lambda x: x.name == 'runTestOnUiThread'
                  and self._isInherited(x),
        action=lambda x: self._replaceString(
            'runTestOnUiThread',
            'InstrumentationRegistry.getInstrumentation().runOnMainSync',
            element=x))

  def changeApis(self):
    def _action(m):
      if (m.name in self.api_mapping[self.super_class_name]['api'] or
        m.name in _SPECIAL_INSTRUMENTATION_TEST_CASE_APIS):
            self._insertInfront(m, self.rule_var+'.')
      elif m.name in self.api_mapping[self.super_class_name].get(
          'special_method_change', {}).keys():
        self._replaceString(
            m.name,
            self.rule_var+'.'+self.api_mapping[self.super_class_name][
                'special_method_change'][m.name],
            element=m,
            optional=False)
      else:
        self.logger.warn('Can NOT handle this method call: %s' %
                          m.name)

    if self.api_mapping and self.api_mapping.get(self.super_class_name):
      self.actionOnMethodInvocation(
          condition=lambda m: self._isInherited(m)
                    and m.name not in _ASSERTION_METHOD_SET
                    and m.name not in _IGNORED_APIS
                    and m.name not in _INSTRUMENTATION_REGISTRY_METHODS,
          action=_action)


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
    def _action(m):
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

    self.actionOnMethodInvocation(
        condition=lambda x: x.name in _ASSERTION_METHOD_SET
                  and x.target is None,
        action=_action)

  def replaceInstrumentationApis(self):
    def _action(m):
      self._insertInfront(m, 'InstrumentationRegistry.')
      self._addImport('android.support.test.InstrumentationRegistry')

    self.actionOnMethodInvocation(
        condition=lambda x: self._isInherited(x)
                  and x.name in _INSTRUMENTATION_REGISTRY_METHODS,
        action=_action)

  def changeSendKeys(self):
    def _action(m):
      self._replaceString(
          r'sendKeys',
          'InstrumentationRegistry.getInstrumentation().sendKeyDownUpSync',
          element=m)
    self.actionOnMethodInvocation(
        condition=lambda x: self._isInherited(x) and x.name == 'sendKeys',
        action=_action)


  def addClassRunner(self):
    self._addImport('org.junit.runner.RunWith')
    self._addImport(self.class_runner()[1])
    self._insertAbove(
        self.main_class, '@RunWith(%s.class)' % self.class_runner()[0])

  def removeExtends(self):
    self._removeImport(self.super_class_name)
    end = '{'
    if self.main_class.implements:
      end = 'implements'
    self._replaceString(r'extends .*? '+end, end, element=self.main_class,
        flags=re.DOTALL)

#     if len(self.rule_dict) != 0:
      # self._addImport(self.rule_dict['package'] + '.'+self.rule_dict['rule'])


  def removeConstructor(self):
    self.actionOnX(model.ConstructorDeclaration,
        action=lambda x: self._replaceString(
            '.*', '', element=x, flags=re.DOTALL), optional=True)

  def changeMinSdkAnnotation(self):
    def _action(a):
      self._replaceString(r'@MinAndroidSdkLevel\((.*)\)', r'@SdkSuppress\1',
          element=a)
      self._removeImport('org.chromium.base.test.util.MinAndroidSdkLevel')
      self._addImport('android.support.test.filters.SdkSuppress')
    self.actionOnX(model.Annotation,
        condition=lambda x: x.name == 'MinAndroidSdkLevel',
        action=_action)

  def addTestAnnotation(self):
    def _action(m):
      self._insertAbove(m, '@Test')
      self._addImport('org.junit.Test')
    self.actionOnMethodDeclaration(condition=lambda x:x.name.startswith('test'),
        action=_action)

  def insertActivityTestRuleTest(self):
    if self.api_mapping and len(self.rule_dict) != 0:
      self._addImport(self.rule_dict['package']+'.'+self.rule_dict['rule'])
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
