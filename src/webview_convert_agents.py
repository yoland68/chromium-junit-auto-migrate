#!/usr/bin/env python

import model
import base_agent
import test_convert_agent

import re
import collections

class WebViewTestAgent(test_convert_agent.TestConvertAgent):
  """Agent for AwTestBase direct childrens"""
  @staticmethod
  def class_runner():
    return ('AwJUnit4ClassRunner',
        'org.chromium.android_webview.test.AwJUnit4ClassRunner')

  @staticmethod
  def raw_api_mapping():
    return {
      "AwTestBase": {
        "package": "org.chromium.android_webview.test",
        "location": "android_webview/javatests/src/org/chromium/android_webvie"
            +"w/test/AwActivityTestRule.java",
        "rule_var": "AwActivityTestRule",
        "rule": "AwActivityTestRule",
        "var": "mActivityTestRule",
        "instan": "AwActivityTestRule()",
        "special_method_change": {},
        "parent_key": None
      },
  }

  @classmethod
  def ignore_files(cls):
    return ['android_webview/javatests/src/org/chromium/android_webview/test/DisableHardwareAccelerationForTest.java']

  def warnAndChangeUiThreadAnnotation(self):
    if any(i for i in self.element_table[model.Annotation]
           if i.name.value == "UiThreadTest"):
      self.logger.warn("There is @UiThreadTestAnnotation in this one")
      self._removeImport('android.test.UiThreadTest')
      self._addImport('android.support.test.annotation.UiThreadTest')

  def skip(self):
    if self.isJUnit4():
      self.logger.debug('Skip: %s is already JUnit4' % self._filepath)
      return True
    if 'abstract' in self.main_class.modifiers:
      self.logger.debug('Skip: %s is abstract class' % self._filepath)
      return True
    if self.api_mapping.get(self.super_class_name) is None:
      self.logger.debug('Skip: mapping does not contain files super class %s'
                       % self.super_class_name)
      return True

  def actions(self):
    #Change setup teardown to be public, remove @Override, add @Before @After
    self.changeSetUpTearDown()

    #Change assertEquals, etc to Assert.assertEquals, import org.junit.Assert
    self.changeAssertions()

    #Replace inherited instrumentation APIs with InstrumentationRegistry apis
    self.replaceInstrumentationApis()

    #Add @RunWith(xxx.class)
    self.addClassRunner()

    #Add @Test to each test
    self.addTestAnnotation()

    #Change runTestOnUiThread() to InstrumentationRegistry.getInstrumentation()
    #.runOnMainSync
    self.changeRunTestOnUiThread()

    #Import all the inherited static types from Rule class
    self.importTypes()

    #Warn in console about classes using @UiThreadTest
    self.warnAndChangeUiThreadAnnotation()

    #Change sendKey() to Instrumentation#sendKeyDownUpSync
    self.changeSendKeys()

    #Remove test class's base class
    self.removeExtends()

    #Insert ActivityTestRule field declaration
    self.insertActivityTestRuleTest()

    #Change all the apis inherited from base class to apis from ActivityTestRule
    self.changeApis()

    #Save file
    self.Save()

