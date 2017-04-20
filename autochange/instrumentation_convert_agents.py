import test_convert_agent
import model

class InstrumentationTestCaseAgent(test_convert_agent.TestConvertAgent):

  def actions(self):
    pass

  @staticmethod
  def ignore_files():
    return []

  @staticmethod
  def raw_api_mapping():
    return {}

  def skip(self):
    if self.isJUnit4():
      self.logger.info('Skip: %s is already JUnit4' % self._filepath)
    if 'abstract' in self.main_class.modifiers:
      self.logger.info('Skip: %s is abstract class' % self._filepath)
      return True
    if self.super_class_name != 'InstrumentationTestCase':
      self.logger.info('Skip: %s is not InstrumentationTestCase direct children'
          % self._filepath)
      return True

  def changeUiThreadTest(self):
    if any(i for i in self.element_table[model.Annotation]
           if i.name.value == "UiThreadTest"):
      self.logger.info("There is @UiThreadTestAnnotation in this one")
      self._removeImport('android.test.UiThreadTest')
      self._addImport('android.support.test.annotation.UiThreadTest')
      if (self.rule_dict is None or
          (self.rule_dict and 'ActivityTestRule' not in
           self.rule_dict['rule'])):
        self._addImport('android.support.test.rule.UiThreadTestRule')
        self._insertActivityTestRule(
            'UiThreadTestRule', 'UiThreadTestRule()',
            'mUiThreadTestRule')
