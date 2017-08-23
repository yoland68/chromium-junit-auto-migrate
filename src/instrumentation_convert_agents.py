import test_convert_agent
import model

class InstrumentationTestCaseAgent(test_convert_agent.TestConvertAgent):
  """Agent for InstrumentationTestCase direct children"""

  def actions(self):
    self.changeSetUpTearDown()
    self.removeExtends()
    self.changeAssertions()
    self.removeConstructor()
    self.replaceInstrumentationApis()
    self.addClassRunner()
    self.addTestAnnotation()
    self.changeRunTestOnUiThread()
    self.changeUiThreadTest()
    self.Save()

  @staticmethod
  def class_runner():
    return ('BaseJUnit4ClassRunner',
            'org.chromium.base.test.BaseJUnit4ClassRunner')

  @classmethod
  def ignore_files(cls):
    return ['android_webview/javatests/src/org/chromium/android_webview/test/DisableHardwareAccelerationForTest.java']

  @staticmethod
  def raw_api_mapping():
    return {}

  def skip(self):
    if self.main_class is None:
      self.logger.debug('Skip: %s is not test java class' % self._filepath)
      return True
    if self.isJUnit4():
      self.logger.debug('Skip: %s is already JUnit4' % self._filepath)
      if 'abstract' in self.main_class.modifiers:
        self.logger.debug('Skip: %s is abstract class' % self._filepath)
        return True
    if self.super_class_name not in ['InstrumentationTestCase', 'AndroidTestCase', 'TestCase']:
      self.logger.debug('Skip: %s is not InstrumentationTestCase direct children'
          % self._filepath)
      return True

  def changeUiThreadTest(self):
    if any(i for i in self.element_table[model.Annotation]
           if i.name.value == "UiThreadTest"):
      self.logger.debug("There is @UiThreadTestAnnotation in this one")
      self._removeImport('android.test.UiThreadTest')
      self._addImport('android.support.test.annotation.UiThreadTest')
      if (self.rule_dict is None or
          (self.rule_dict and 'ActivityTestRule' not in
           self.rule_dict['rule'])):
        self._addImport('android.support.test.rule.UiThreadTestRule')
        self._insertActivityTestRule(
            'UiThreadTestRule', 'UiThreadTestRule()',
            'mUiThreadTestRule')
  #override
  @classmethod
  def filename_match(cls, wholepath):
    if (wholepath.endswith('.java') and 'Test' in wholepath and
        wholepath not in cls.ignore_files()):
      return True
    return False

