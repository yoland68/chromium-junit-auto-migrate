#!/usr/bin/env python

import model
import base_agent
import test_convert_agent

import re

_TOUCH_COMMON_METHOD_DICT = {
    'dragStart': True,
    'dragTo': True,
    'dragEnd': True,
    'singleClickView': False
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

  def addCommandLineFlags(self):
    commandline_template = \
        """@CommandLineFlags.Add({ChromeSwitches.DISABLE_FIRST_RUN_EXPERIENCE,
        ChromeActivityTestRule.DISABLE_NETWORK_PREDICTION_FLAG,
        %s})"""
    values = []
    flags = self.actionOnX(
        model.Annotation,
        condition=lambda x:x.name.value == "CommandLineFlags.Add" and
                  self.content[self._lexposToLoc(x.lexpos)-1] == '\n',
        optional=True)
    if flags:
      existing_flag = flags[0]
      if (isinstance(existing_flag.single_member, model.Name)
          or isinstance(existing_flag.single_member, model.Literal)):
        values.append(existing_flag.single_member.value)
      else:
        for lit in existing_flag.single_member.elements:
          values.append(lit.value)
      self._removeElement(existing_flag)
    self._addImport("org.chromium.chrome.browser.ChromeSwitches")
    self._addImport("org.chromium.chrome.test.ChromeActivityTestRule")
    self._addImport("org.chromium.base.test.util.CommandLineFlags")
    self._insertAbove(
        self.main_class, commandline_template % ", \n        ".join(values))

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
        self._insertAbove(start_m, '@Before')
        self._addImport('org.junit.Before')
        self._replaceString(r' *@Override\n', '', element=start_m,
                            optional=True)
        self._replaceString('startMainActivity', 'setUp', element=start_m,
                            optional=False)
    else:
      # If startMainActivity() exist but is empty, remove it
      if start_m:
        self._removeElement(start_m)
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
      if _TOUCH_COMMON_METHOD_DICT[m.name]:
        replacement = r'TouchCommon.\1%s.getActivity(), ' % self.rule_dict['var']
      else:
        replacement = r'TouchCommon.\1'

      self._replaceString(
          '('+m.name+'\()', replacement, element=m, optional=False)
      self._addImport('org.chromium.content.browser.test.util.TouchCommon')
    self.actionOnMethodInvocation(
        condition=lambda x:self._isInherited(x) and
                  x.name in _TOUCH_COMMON_METHOD_DICT.keys(),
        action=_action)

  def warnAndChangeUiThreadAnnotation(self):
    if any(i for i in self.element_table[model.Annotation]
           if i.name.value == "UiThreadTest"):
      self.logger.warn("There is @UiThreadTestAnnotation in this one")
      self._removeImport('android.test.UiThreadTest')
      self._addImport('android.support.test.annotation.UiThreadTest')

  def addExtraImports(self):
    self._addImport('org.chromium.chrome.browser.ChromeTabbedActivity')

  def actions(self):
    self.changeSetUpTearDown()
    self.SaveAndReload()
    self.changeAssertions()
    self.replaceInstrumentationApis()
    self.addClassRunner()
    self.addTestAnnotation()
    self.changeRunTestOnUiThread()
    self.importTypes()
    self.addCommandLineFlags()
    self.warnAndChangeUiThreadAnnotation()
    self.changeSendKeys()
    self.changeTouchCommonMethods()
    self.removeExtends()
    self.insertActivityTestRuleTest()
    self.changeApis()
    self.addExtraImports()
    self.Save()

  @staticmethod
  def class_runner():
    return ('ChromeJUnit4ClassRunner',
        'org.chromium.chrome.test.ChromeJUnit4ClassRunner')

  @staticmethod
  def raw_api_mapping():
    return {
      "ChromeActivityTestCaseBase": {
        "package": "org.chromium.chrome.test",
        "location": "chrome/test/android/javatests/src/org/chromium/chrome/test"
            +"/ChromeActivityTestRule.java",
        "rule_var": "ChromeActivityTestRule<ChromeActivity>",
        "rule": "ChromeActivityTestRule",
        "var": "mActivityTestRule",
        "instan": "ChromeActivityTestRule<>(ChromeActivity.class)",
        "special_method_change": {}
      },
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

class ChromeTabbedTestAgent(ChromeActivityBaseCaseAgent):
  @staticmethod
  def raw_api_mapping():
    raw_api = {
      "ChromeTabbedActivityTestBase": {
        "package": "org.chromium.chrome.test",
        "location": "chrome/test/android/javatests/src/org/chromium/chrome/test"
            "/ChromeTabbedActivityTestRule.java",
        "rule_var": "ChromeTabbedActivityTestRule",
        "rule": "ChromeTabbedActivityTestRule",
        "var": "mActivityTestRule",
        "instan": "ChromeTabbedActivityTestRule()",
        "special_method_change": {}
      }
    }
    raw_api.update(ChromeActivityBaseCaseAgent.raw_api_mapping())
    return raw_api

  def skip(self):
    if self.super_class_name != "ChromeTabbedActivityTestBase":
      self.logger.info('Skip: %s is not ChromeTabbedActivityTestBase children'
                       % self._filepath)
      return True
    return super(ChromeTabbedTestAgent, self).skip()

class PermissionTestAgent(ChromeActivityBaseCaseAgent):
  @staticmethod
  def raw_api_mapping():
    raw_api = {
			"PermissionTestCaseBase": {
        "package": "org.chromium.chrome.permission",
        "location": "chrome/android/javatests/src/org/chromium/chrome/browser"
            +"/permissions/PermissionTestCaseBase.java",
        "rule_var": "PermissionTestRule",
        "rule": "PermissionTestRule",
        "var": "mPermissionRule",
        "instan": "PermissionTestRule()",
        "special_method_change": {}
      }
    }
    raw_api.update(ChromeActivityBaseCaseAgent.raw_api_mapping())
    return raw_api

  def skip(self):
    if self.super_class_name != "PermissionTestCaseBase":
      self.logger.info('Skip: %s is not PermissionTestCaseBase children'
                       % self._filepath)
      return True
    return super(PermissionTestAgent, self).skip()

class MultiActivityTestAgent(ChromeActivityBaseCaseAgent):
  @staticmethod
  def raw_api_mapping():
    raw_api = {
			"MultiActivityTestBase": {
        "package": "org.chromium.chrome.test",
        "location": "chrome/test/android/javatests/src/org/chromium/chrome/test"
            +"/MultiActivityTestBase.java",
        "rule_var": "MultiActivityTestRule",
        "rule": "MultiActivityTestRule",
        "var": "mTestRule",
        "instan": "MultiActivityTestRule()",
        "special_method_change": {}
      }
    }
    raw_api.update(ChromeActivityBaseCaseAgent.raw_api_mapping())
    return raw_api

  def skip(self):
    if self.super_class_name != "MultiActivityTestBase":
      self.logger.info('Skip: %s is not MultiActivityTestBase children'
                       % self._filepath)
      return True
    return super(MultiActivityTestAgent, self).skip()

class TempChromeBaseRefactorAgent(ChromeActivityBaseCaseAgent):
  def skip(self):
    if not self.isJUnit4():
      self.logger.info('Skip: %s is not JUnit4' % self._filepath)
      return True
    if 'abstract' in self.main_class.modifiers:
      self.logger.info('Skip: %s is abstract class' % self._filepath)
      return True
    return False

  def actions(self):
    replacement = "@CommandLineFlags(ChromeActivityTestRule.DefaultFlags)"
    def condition(a):
      if not isinstance(a.single_member, model.ArrayInitializer):
        return False
      else:
        flags = [n.value for n in a.single_member.elements
                 if isinstance(n, model.Name)]
        if (len(flags) == 2 and
            'ChromeSwitches.DISABLE_FIRST_RUN_EXPERIENCE' in flags and
            'ChromeActivityTestRule.DISABLE_NETWORK_PREDICTION_FLAG' in flags):
          return True
        else:
          return False

    def _action(a):
      self._insertAbove(a, replacement)
      self._removeElement(a)
    self.actionOnX(model.Annotation, condition=condition, action=_action)
    self.Save()
