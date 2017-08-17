#!/usr/bin/env python

import model
import base_agent
import test_convert_agent

import re
import collections

_TOUCH_COMMON_METHOD_DICT = {
    'dragStart': True,
    'dragTo': True,
    'dragEnd': True,
    'singleClickView': False
}

class CronetTestAgent(test_convert_agent.TestConvertAgent):
  """Agent for CronetTestBase direct childrens"""
  @staticmethod
  def class_runner():
    return ('BaseJUnit4ClassRunner',
            'org.chromium.base.test.BaseJUnit4ClassRunner')

  def skip(self):
    if self.isJUnit4():
      self.logger.debug('Skip: %s is already JUnit4' % self._filepath)
    if self.main_class is None:
      self.logger.debug('Skip: %s is not a java class' % self._filepath)
      return True
    if 'abstract' in self.main_class.modifiers:
      self.logger.debug('Skip: %s is abstract class' % self._filepath)
      return True
    if self.super_class_name != 'CronetTestBase':
      self.logger.debug('Skip: %s is not CronetTestAgent direct children'
          % self._filepath)
      return True
    return False

  @staticmethod
  def raw_api_mapping():
    return {
      "CronetTestBase": {
        "package": "org.chromium.net",
        "location": "components/cronet/android/test/javatests/src/org/chromium"
          + "/net/CronetTestBase.java",
        "rule_var": "CronetTestRule",
        "rule": "CronetTestRule",
        "var": "mTestRule",
        "instan": "CronetTestRule()",
        "special_method_change": {},
        "parent_key": None
      }
    }

  @classmethod
  def ignore_files(cls):
    return []

  def actions(self):
    self.changeSetUpTearDown()
    self.removeExtends()
    self.changeAssertions()
    self.removeConstructor()
    self.replaceInstrumentationApis()
    self.addClassRunner()
    self.addTestAnnotation()
    self.warnAndChangeUiThreadAnnotation()
    self.changeRunTestOnUiThread()
    self.importTypes()
    self.insertActivityTestRuleTest()
    self.changeApis()
    self.Save()

class PartnerUnitTestAgent(test_convert_agent.TestConvertAgent):
  """Agent for BasePartnerBrowserCustomizationUnitTest direct childrens"""
  @staticmethod
  def class_runner():
    return ('BaseJUnit4ClassRunner',
            'org.chromium.base.test.BaseJUnit4ClassRunner')

  @classmethod
  def ignore_files(cls):
    return []

  def skip(self):
    if self.isJUnit4():
      self.logger.debug('Skip: %s is already JUnit4' % self._filepath)
    if self.main_class is None:
      self.logger.debug('Skip: %s is not a java class' % self._filepath)
      return True
    if 'abstract' in self.main_class.modifiers:
      self.logger.debug('Skip: %s is abstract class' % self._filepath)
      return True
    if self.super_class_name != 'BasePartnerBrowserCustomizationUnitTest':
      self.logger.debug('Skip: %s is not CronetTestAgent direct children'
          % self._filepath)
      return True
    return False

  @staticmethod
  def raw_api_mapping():
    return {
      "BasePartnerBrowserCustomizationUnitTest": {
        "package": "org.chromium.chrome.browser.partnercustomizations",
        "location": "chrome/android/javatests/src/org/chromium/chrome/browser/"
          + "partnercustomizations/BasePartnerBrowserCustomizationUnitTestRule.java",
        "rule_var": "BasePartnerBrowserCustomizationUnitTestRule",
        "rule": "BasePartnerBrowserCustomizationUnitTestRule",
        "var": "mTestRule",
        "instan": "BasePartnerBrowserCustomizationUnitTestRule()",
        "special_method_change": {"getContext": "getContextWrapper"},
        "parent_key": None
      }
    }

  def actions(self):
    self.insertActivityTestRuleTest()
    self.changeApis()
    self.changeSetUpTearDown()
    self.removeExtends()
    self.changeAssertions()
    self.removeConstructor()
    self.replaceInstrumentationApis()
    self.addClassRunner()
    self.addTestAnnotation()
    self.warnAndChangeUiThreadAnnotation()
    self.changeRunTestOnUiThread()
    self.importTypes()
    self.Save()

class CrashTestAgent(test_convert_agent.TestConvertAgent):
  """Agent for CrashTestCase direct childrens"""
  @staticmethod
  def class_runner():
    return ('BaseJUnit4ClassRunner',
            'org.chromium.base.test.BaseJUnit4ClassRunner')

  @classmethod
  def ignore_files(cls):
    return []

  def skip(self):
    if self.isJUnit4():
      self.logger.debug('Skip: %s is already JUnit4' % self._filepath)
    if self.main_class is None:
      self.logger.debug('Skip: %s is not a java class' % self._filepath)
      return True
    if 'abstract' in self.main_class.modifiers:
      self.logger.debug('Skip: %s is abstract class' % self._filepath)
      return True
    if self.super_class_name != 'CrashTestCase':
      self.logger.debug('Skip: %s is not CronetTestAgent direct children'
          % self._filepath)
      return True
    return False

  @staticmethod
  def raw_api_mapping():
    return {
      "CrashTestCase": {
        "package": "org.chromium.components.minidump_uploader",
        "location": "components/minidump_uploader/android/javatests/src/org/chromium/components/minidump_uploader/CrashTestRule.java",
        "rule_var": "CrashTestRule",
        "rule": "CrashTestRule",
        "var": "mTestRule",
        "instan": "CrashTestRule()",
        "special_method_change": {},
        "parent_key": None
      }
    }

  def actions(self):
    self.insertActivityTestRuleTest()
    self.changeApis()
    self.changeSetUpTearDown()
    self.removeExtends()
    self.changeAssertions()
    self.removeConstructor()
    self.replaceInstrumentationApis()
    self.addClassRunner()
    self.addTestAnnotation()
    self.warnAndChangeUiThreadAnnotation()
    self.changeRunTestOnUiThread()
    self.importTypes()
    self.Save()


class ChromeActivityBaseCaseAgent(test_convert_agent.TestConvertAgent):
  """Agent for ChromeActivityTestCaseBase direct childrens"""
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
        "special_method_change": {},
        "parent_key": None
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
      self.logger.debug('Skip: %s is already JUnit4' % self._filepath)
      return True
    if self.main_class is None:
      self.logger.debug('Skip: %s is not a java class' % self._filepath)
      return True
    if 'abstract' in self.main_class.modifiers:
      self.logger.debug('Skip: %s is abstract class' % self._filepath)
      return True
    if self.api_mapping.get(self.super_class_name) is None:
      self.logger.debug('Skip: mapping does not contain files super class %s'
                       % self.super_class_name)
      return True

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

  def addCommandLineFlags(self, template=None):
    if template is None:
      commandline_template = \
          """@CommandLineFlags.Add({ChromeSwitches.DISABLE_FIRST_RUN_EXPERIENCE,
          ChromeActivityTestRule.DISABLE_NETWORK_PREDICTION_FLAG,
          %s})"""
    else:
      commandline_template = template
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

  def addExtraImports(self):
    self._addImport('org.chromium.chrome.browser.ChromeTabbedActivity')

  def actions(self):
    #Change setup teardown to be public, remove @Override, add @Before @After
    self.changeSetUpTearDown()

    #Save the file and re-parse it
    self.SaveAndReload()

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

    #Add or modify @CommandLineFlags
    self.addCommandLineFlags()

    #Warn in console about classes using @UiThreadTest
    self.warnAndChangeUiThreadAnnotation()

    #Change sendKey() to Instrumentation#sendKeyDownUpSync
    self.changeSendKeys()

    #Change singleViewClick, dragTo, etc to TouchCommon.singleViewClick
    self.changeTouchCommonMethods()

    #Remove test class's base class
    self.removeExtends()

    #Insert ActivityTestRule field declaration
    self.insertActivityTestRuleTest()

    #Change all the apis inherited from base class to apis from ActivityTestRule
    self.changeApis()

    #Import static variables
    #self.importStaticVariables()

    #Import any extra classes needed
    self.addExtraImports()

    #Save file
    self.Save()

class SyncTestAgent(ChromeActivityBaseCaseAgent):
  """Agent for SyncTestBase direct childrens"""
  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["SyncTestBase"] = {
        "package": "org.chromium.chrome.permission",
        "location": "chrome/android/sync_shell/javatests/src/org/chromium/chrome/browser"
            +"/sync/SyncTestBase.java",
        "rule_var": "SyncTestRule",
        "rule": "SyncTestRule",
        "var": "mSyncTestRule",
        "instan": "SyncTestRule()",
        "parent_key": base_mapping.keys()[0],
        "special_method_change": {}
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "SyncTestBase":
      self.logger.debug('Skip: %s is not SyncTestBase children'
                       % self._filepath)
      return True
    return super(SyncTestAgent, self).skip()

class PartnerIntegrationTestAgent(ChromeActivityBaseCaseAgent):
  """Agent for BasePartnerBrowserCustomizationIntegrationTest direct childrens"""
  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["BasePartnerBrowserCustomizationIntegrationTest"] = {
        "package": "org.chromium.chrome.browser.partnercustomizations",
        "location": "chrome/android/javatests/src/org/chromium/chrome/browser/"
          + "partnercustomizations/BasePartnerBrowserCustomizationIntegrationTestRule.java",
        "rule_var": "BasePartnerBrowserCustomizationIntegrationTestRule",
        "rule": "BasePartnerBrowserCustomizationIntegrationTestRule",
        "var": "mActivityTestRule",
        "instan": "BasePartnerBrowserCustomizationIntegrationTestRule()",
        "parent_key": base_mapping.keys()[0],
        "special_method_change": {}
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "BasePartnerBrowserCustomizationIntegrationTest":
      self.logger.debug('Skip: %s is not BasePartnerBrowserCustomizationIntegrationTest children'
                       % self._filepath)
      return True
    return super(PartnerIntegrationTestAgent, self).skip()

class ChromeTabbedTestAgent(ChromeActivityBaseCaseAgent):
  """Agent for ChromeTabbedTestCase direct childrens"""
  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["ChromeTabbedActivityTestBase"] = {
      "package": "org.chromium.chrome.test",
      "location": "chrome/test/android/javatests/src/org/chromium/chrome/test"
          "/ChromeTabbedActivityTestRule.java",
      "rule_var": "ChromeTabbedActivityTestRule",
      "rule": "ChromeTabbedActivityTestRule",
      "var": "mActivityTestRule",
      "parent_key": base_mapping.keys()[0],
      "instan": "ChromeTabbedActivityTestRule()",
      "special_method_change": {},
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "ChromeTabbedActivityTestBase":
      self.logger.debug('Skip: %s is not ChromeTabbedActivityTestBase children'
                       % self._filepath)
      return True
    return super(ChromeTabbedTestAgent, self).skip()

class PermissionTestAgent(ChromeActivityBaseCaseAgent):
  """Agent for PermissionTestBase direct childrens"""
  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["PermissionTestCaseBase"] = {
        "package": "org.chromium.chrome.permission",
        "location": "chrome/android/javatests/src/org/chromium/chrome/browser"
            +"/permissions/PermissionTestCaseBase.java",
        "rule_var": "PermissionTestRule",
        "rule": "PermissionTestRule",
        "var": "mPermissionRule",
        "instan": "PermissionTestRule()",
        "parent_key": base_mapping.keys()[0],
        "special_method_change": {}
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "PermissionTestCaseBase":
      self.logger.debug('Skip: %s is not PermissionTestCaseBase children'
                       % self._filepath)
      return True
    return super(PermissionTestAgent, self).skip()


class ChromeVrTestAgent(ChromeActivityBaseCaseAgent):
  """Agent for VrTestBase direct childrens"""
  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["VrTestBase"] = {
      "package": "org.chromium.chrome.browser.vr_shell",
      "location": "chrome/android/javatests/src/org/chromium/chrome/browser/"
          +"vr_shell/VrTestRule.java",
      "rule_var": "VrTestRule",
      "rule": "VrTestRule",
      "var": "mVrTestRule",
      "instan": "VrTestRule()",
      "parent_key": base_mapping.keys()[0],
      "special_method_change": {}
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "VrTestBase":
      self.logger.debug('Skip: %s is not VrTestBase children'
                       % self._filepath)
      return True
    return super(ChromeVrTestAgent, self).skip()


class MultiActivityTestAgent(ChromeActivityBaseCaseAgent):
  """Agent for MultiActivityTestBase direct children"""

  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["MultiActivityTestBase"] = {
        "package": "org.chromium.chrome.test",
        "location": "chrome/test/android/javatests/src/org/chromium/chrome/test"
            +"/MultiActivityTestBase.java",
        "rule_var": "MultiActivityTestRule",
        "rule": "MultiActivityTestRule",
        "var": "mTestRule",
        "instan": "MultiActivityTestRule()",
        "parent_key": base_mapping.keys()[0],
        "special_method_change": {}
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "MultiActivityTestBase":
      self.logger.debug('Skip: %s is not MultiActivityTestBase children'
                       % self._filepath)
      return True
    return super(MultiActivityTestAgent, self).skip()


class PaymentRequestAgent(ChromeActivityBaseCaseAgent):
  """Agent for PaymentRequestTestBase direct childrens"""
  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["PaymentRequestTestBase"] = {
        "package": "org.chromium.chrome.payments",
        "location": "chrome/android/javatests/src/org/chromium/chrome/browser"
            +"/payments/PaymentRequestTestBase.java",
        "rule_var": "PaymentRequestTestRule",
        "rule": "PaymentRequestTestRule",
        "var": "mPaymentRequestTestRule",
        "instan": "PaymentRequestTestRule(%s, this)",
        "parent_key": base_mapping.keys()[0],
        "special_method_change": {}
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "PaymentRequestTestBase":
      self.logger.debug('Skip: %s is not PaymentRequestTestBase children'
                       % self._filepath)
      return True
    return super(PaymentRequestAgent, self).skip()

  def removeConstructorParameterToRuleInsta(self):
    def _action(constu):
      content = self._replaceString(r'.*', '', element=constu, flags=re.DOTALL)
      argument = re.search(r'.*super\((".*?")\);.*', content, flags=re.DOTALL).group(1)
      self.rule_dict['modified_instan'] = self.rule_dict['instan'] % argument
    self.actionOnX(model.ConstructorDeclaration, action=_action)

  def implementMainActivityStartCallback(self):
    self._replaceString(
        r'^(public.*?) {',
        r'\1 implements MainActivityStartCallback {',
        element=self.main_class,
        flags=re.DOTALL)

  def actions(self):
    self.removeConstructorParameterToRuleInsta()
    self.implementMainActivityStartCallback()
    self.SaveAndReload()
    super(PaymentRequestAgent, self).actions()

class CastTestAgent(ChromeActivityBaseCaseAgent):
  """Agent for CastTestBase direct childrens"""
  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["CastTestBase"] = {
        "package": "org.chromium.chrome.browser.media.remote",
        "location": "chrome/android/javatests/src/org/chromium/chrome/browser"
            +"/media/remote/CastTestRule.java",
        "rule_var": "CastTestRule",
        "rule": "CastTestRule",
        "var": "mCastTestRule",
        "instan": "CastTestRule()",
        "parent_key": base_mapping.keys()[0],
        "special_method_change": {}
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "CastTestBase":
      self.logger.debug('Skip: %s is not CastTestBase children'
                       % self._filepath)
      return True
    return super(CastTestAgent, self).skip()

class ProviderTestAgent(ChromeActivityBaseCaseAgent):
  """Agent for ProviderTestBase direct childrens"""
  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["ProviderTestBase"] = {
        "package": "org.chromium.chrome.browser.provider",
        "location": "chrome/android/javatests/src/org/chromium/chrome/browser"
            +"/provider/ProviderTestRule.java",
        "rule_var": "ProviderTestRule",
        "rule": "ProviderTestRule",
        "var": "mProviderTestRule",
        "instan": "ProviderTestRule()",
        "parent_key": base_mapping.keys()[0],
        "special_method_change": {}
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "ProviderTestBase":
      self.logger.debug('Skip: %s is not ProviderTestBase children'
                       % self._filepath)
      return True
    return super(ProviderTestAgent, self).skip()

class CustomTabActivityTestAgent(ChromeActivityBaseCaseAgent):
  """Agent for CustomTabActivityTestBase direct childrens"""
  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["CustomTabActivityTestBase"] = {
        "package": "org.chromium.chrome.browser.customtabs",
        "location": "chrome/android/javatests/src/org/chromium/chrome/browser"
            +"/customtabs/CustomTabActivityTestRule.java",
        "rule_var": "CustomTabActivityTestRule",
        "rule": "CustomTabActivityTestRule",
        "var": "mCustomTabActivityTestRule",
        "instan": "CustomTabActivityTestRule()",
        "parent_key": base_mapping.keys()[0],
        "special_method_change": {}
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "CustomTabActivityTestBase":
      self.logger.debug('Skip: %s is not CustomTabActivityTestBase children'
                       % self._filepath)
    return super(CustomTabActivityTestAgent, self).skip()

class NotificationTestAgent(ChromeActivityBaseCaseAgent):
  """Agent for NotificationTestBase direct childrens"""
  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["NotificationTestBase"] = {
        "package": "org.chromium.chrome.browser.notifications",
        "location": "chrome/android/javatests/src/org/chromium/chrome/browser"
            +"/notifications/NotificationTestRule.java",
        "rule_var": "NotificationTestRule",
        "rule": "NotificationTestRule",
        "var": "mNotificationTestRule",
        "instan": "NotificationTestRule()",
        "parent_key": base_mapping.keys()[0],
        "special_method_change": {}
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "NotificationTestBase":
      self.logger.debug('Skip: %s is not NotificationTestBase children'
                       % self._filepath)
      return True
    return super(NotificationTestAgent, self).skip()

class DownloadTestAgent(ChromeActivityBaseCaseAgent):
  """Agent for DownloadTestBase direct childrens"""
  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["DownloadTestBase"] = {
        "package": "org.chromium.chrome.browser.download",
        "location": "chrome/android/javatests/src/org/chromium/chrome/browser"
            +"/download/DownloadTestRule.java",
        "rule_var": "DownloadTestRule",
        "rule": "DownloadTestRule",
        "var": "mDownloadTestRule",
        "instan": "DownloadTestRule()",
        "parent_key": base_mapping.keys()[0],
        "special_method_change": {}
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "DownloadTestBase":
      self.logger.debug('Skip: %s is not DownloadTestBase children'
                       % self._filepath)
      return True
    return super(DownloadTestAgent, self).skip()

class BottomSheetTestAgent(ChromeActivityBaseCaseAgent):
  """Agent for BottomSheetTestCaseBase direct childrens"""
  @staticmethod
  def raw_api_mapping():
    result_mapping = collections.OrderedDict()
    base_mapping = ChromeActivityBaseCaseAgent.raw_api_mapping()
    result_mapping["BottomSheetTestCaseBase"] = {
        "package": "org.chromium.chrome.browser.provider",
        "location": "chrome/test/android/javatests/src/org/chromium/chrome/"
            +"test/BottomSheetTestRule.java",
        "rule_var": "BottomSheetTestRule",
        "rule": "BottomSheetTestRule",
        "var": "mBottomSheetTestRule",
        "instan": "BottomSheetTestRule()",
        "parent_key": base_mapping.keys()[0],
        "special_method_change": {}
    }
    result_mapping.update(base_mapping)
    return result_mapping

  def skip(self):
    if self.super_class_name != "BottomSheetTestCaseBase":
      self.logger.debug('Skip: %s is not BottomSheetTestCaseBase children'
                       % self._filepath)
      return True
    return super(BottomSheetTestAgent, self).skip()

  def addCommandLineFlags(self, template=None):
    template = \
          """@CommandLineFlags.Add({ChromeSwitches.DISABLE_FIRST_RUN_EXPERIENCE,
          ChromeActivityTestRule.DISABLE_NETWORK_PREDICTION_FLAG,
          enable-features=ChromeHome,
          %s})"""

    super(BottomSheetTestAgent, self).addCommandLineFlags(template)

  def addRestrictionAnnotation(self):
    self._insertAbove(
        self.main_class,
        "@Restriction(RESTRICTION_TYPE_PHONE) // ChromeHome is only enabled \
              on phones")

  def actions(self):
    self.addRestrictionAnnotation()
    super(BottomSheetTestAgent, self).actions()



