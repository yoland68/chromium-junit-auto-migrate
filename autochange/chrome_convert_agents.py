#!/usr/bin/env python

import model
import base_agent
import test_convert_agent

import re

_TOUCH_COMMON_METHOD_DICT = {
    'dragStart': True,
    'dragTo': True,
    'dragEnd': True,
    'singleClick': False
}

class ChromeActivityBaseCaseAgent(test_convert_agent.TestConvertAgent):
  def _activityLaunchReplacement(self, m):
    if len(m.body) == 0:
      return ''
    start = self._lexposToLoc(m.body[0].lexpos)
    end = self._lexposToLoc(m.body[-1].lexend)
    content = self.content[start:end+1]
    self._replaceString(r'.*', '', element=m, flags=re.DOTALL)
    return content

  def _startActivityEmpty(self, declaration):
    if (not declaration) or len(declaration.body) == 0:
      return True
    else:
      return False

  def _convertSetUp(self, m, replacement=''):
    self._replaceString('protected', 'public', element=m, optional=True)
    self._insertAbove(m, '@Before')
    self._addImport('org.junit.Before')
    self._replaceString(r' *@Override\n', '', element=m, optional=True)
    self._replaceString(
        r' *super.setUp\(.*\); *\n', replacement, element=m, optional=True)

  def changeSetUpTearDown(self):
    methods = dict(
        (m.name, m) for m in self.element_table[model.MethodDeclaration]
        if m.name in ['setUp', 'tearDown', 'startMainActivity'])

    # If startMainActivity() declaration exists, it may be copied over to setUp
    # or become setUp straight up depending on setUp() exists
    start_m = methods.get('startMainActivity')
    m = methods.get('setUp')
    if not self._startActivityEmpty(start_m):
      if m:
        start_main_activity_body = self._activityLaunchReplacement(start_m)
        self._convertSetUp(m, replacement=start_main_activity_body)
      else:
        self._insertAbove(m, '@Before')
        self._addImport('org.junit.Before')
        self._replaceString(r' *@Override\n', '', element=start_m,
                            optional=True)
        self._replaceString('startMainActivity', 'setUp', element=start_m,
                            optional=False)
    else:
      # If startMainActivity() exist but is empty, remove it
      if start_m:
        self._activityLaunchReplacement(start_m)
      if m:
        self._convertSetUp(m)

    if methods.get('tearDown'):
      m = methods.get('tearDown')
      self._replaceString('protected', 'public', element=m, optional=True)
      self._insertAbove(m, '@After')
      self._addImport('org.junit.After')
      self._replaceString(r' *@Override\n', '', element=m, optional=True)
      self._replaceString(
          r' *super.tearDown\(.*\) *;\n', '', element=m, optional=True)


  def changeTouchCommonMethods(self):
    def _action(m):
      self._replaceString('('+m.name+'\()',
          r'TouchCommon.\1mActivityTestRule.getActivity(), '
          % self.rule_dict['var'] if _TOUCH_COMMON_METHOD_DICT[m.name]
          else r'TouchCommon.\1', element=m, optional=False)
      self._addImport('org.chromium.content.browser.test.util.TouchCommon')
    self.actionOnMethodInvocation(
        condition=lambda x:self._isInherited(x) and
                  x.name in _TOUCH_COMMON_METHOD_DICT,
        action=_action)

  def warnAndChangeUiThreadAnnotation(self):
    if any(i for i in self.element_table[model.Annotation]
           if i.name.value == "UiThreadTest"):
      self.logger.warn("There is @UiThreadTestAnnotation in this one")
      self._removeImport('android.test.UiThreadTest')
      self._addImport('android.support.test.annotation.UiThreadTest')

  def actions(self):
    self.changeSetUpTearDown()
    self.SaveAndReload()
    self.changeAssertions()
    self.removeConstructor()
    self.replaceInstrumentationApis()
    self.addClassRunner()
    self.addTestAnnotation()
    self.changeRunTestOnUiThread()
    self.importTypes()
    self.warnAndChangeUiThreadAnnotation()
    self.removeExtends()
    self.insertActivityTestRuleTest()
    self.changeApis()
    self.Save()

  @staticmethod
  def class_runner():
    return 'ChromeJUnit4ClassRunner'

  @staticmethod
  def raw_api_mapping():
    return {
      "ChromeActivityTestCaseBase": {
        "package": "org.chromium.chrome.test",
        "location": "chrome/test/android/javatests/src/org/chromium/chrome/test\
            /ChromeActivityTestRule.java",
        "rule_var": "ChromeActivityTestRule<ChromeActivity>",
        "rule": "ChromeActivityTestRule",
        "var": "mActivityTestRule",
        "instan": "ChromeActivityTestRule<>(ChromeActivity.class)"
      }
  }

  @classmethod
  def ignore_files(cls):
    return [
      "chrome/android/javatests/src/org/chromium/chrome/test/util/parameters/\
          SigninParametersTest.java",
      "chrome/android/javatests/src/org/chromium/chrome/browser/webapps/\
          WebApkIntegrationTest.java"
    ]

  def skip(self):
    if self.isJUnit4():
      self.logger.info('Skip: %s is already JUnit4' % self._filepath)
      return True
    if 'abstract' in self.main_class.modifiers:
      self.logger.info('Skip: %s is abstract class' % self._filepath)
      return True
    if self.api_mapping.get(self.super_class_name) is None:
      self.logger.info('Skip: mapping does not contain files super class %s'
                       % self.super_class_name)
      return True
