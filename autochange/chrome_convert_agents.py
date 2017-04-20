#!/usr/bin/env python

import model
import base_agent
import test_convert_agent

_TOUCH_COMMON_METHOD_DICT = {
    'dragStart': True,
    'dragTo': True,
    'dragEnd': True,
    'singleClick': False
}

class ChromeActivityBaseCaseAgent(test_convert_agent.TestConvertAgent):
  def changeTouchCommonMethods(self):
    for m in self.element_table.get(model.MethodInvocation, []):
      if m.target is None and m.name in _TOUCH_COMMON_METHOD_DICT.keys():
          self._replaceString('('+m.name+'\()',
              r'TouchCommon.\1mActivityTestRule.getActivity(), '
              % self.rule_dict['var'] if _TOUCH_COMMON_METHOD_DICT[m.name]
              else r'TouchCommon.\1', element=m, optional=False)
          self._addImport('org.chromium.content.browser.test.util.TouchCommon')

  def warnAboutUiThreadAnnotation(self):
    if any(i for i in self.element_table[model.Annotation]
           if i.name.value == "UiThreadTest"):
      self.logger.warn("There is @UiThreadTestAnnotation in this one")



  def actions(self):
    self.changeSetUp()
    self.SaveAndReload()
    self.changeAssertions()
    self.removeConstructor()
    self.replaceInstrumentationApis()
    self.addClassRunner()
    self.addTestAnnotation()
    self.changeMinSdkAnnotation()
    self.changeRunTestOnUiThread()
    self.importTypes()
    self.changeUiThreadTest()
    self.removeExtends()
    self.insertActivityTestRuleTest()
    self.changeApis()
    self.Save()

  @staticmethod
  def raw_api_mapping():
    return {
      "ChromeActivityTestCaseBase": {
        "package": "org.chromium.chrome.test",
        "location": "chrome/test/android/javatests/src/org/chromium/chrome/test/ChromeActivityTestRule.java",
        "rule_var": "ChromeActivityTestRule<ChromeActivity>",
        "rule": "ChromeActivityTestRule",
        "var": "mActivityTestRule",
        "instan": "ChromeActivityTestRule<>(ChromeActivity.class)"
      }
  }

  @staticmethod
  def ignore_files():
    return [
      "chrome/android/javatests/src/org/chromium/chrome/test/util/parameters/SigninParametersTest.java",
      "chrome/android/javatests/src/org/chromium/chrome/browser/webapps/WebApkIntegrationTest.java"
    ]

  def skip(self):
    if self.isJUnit4():
      self.logger.info('Skip: %s is already JUnit4' % self._filepath)
      return True
    if 'abstract' in self.main_class.modifiers:
      self.logger.info('Skip: %s is abstract class' % self._filepath)
      return True
    if self.api_mapping.get(self.super_class_name) is None:
      self.logger.info('Skip: mapping does not contain files super class %s' % self.super_class_name)
      return True
