#!/usr/bin/env python

import model
import test_convert_agent
import base_agent

import codecs
import jinja2
import logging
import re
import os

_TEST_COMMON_JINJA_TEMPLATE = """
// Copyright 2017 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package {{ package }};

{%for i in imports%}
{{ i }}
{% endfor %}

// TODO(yolandyan): move this class to its test rule once JUnit4 migration is over
final class {{classname}} {
    {% for f in fields %}
      {{ f }}
    {% endfor %}
    private final {{common_callback}} mCallback;

    {{classname}}({{common_callback}} callback) {
        mCallback = callback;
    }

    {% for m in methods %}
      {{ m }}
    {% endfor %}

    public interface {{common_callback}} {
      //FILL_CALLBACK
    }
}
"""

_TEST_RULE_JINJA_TEMPLATE = """

// Copyright 2017 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package {{ package }};

{%for i in imports%}
{{ i }}
{% endfor %}

public class {{classname}} extends FILL_SUPER implements {{common_callback}} {
    {% for f in fields %}
      {{ f }}
    {% endfor %}

    private final {{testcommon}} mTestCommon;

    public {{classname}}(Class<> activityClass) {
        super(activityClass);
        mTestCommon = new {{testcommon}}(this);
    }

    {% for m in methods %}
      {{ m }}
    {% endfor %}
}
"""


class BaseCaseAgent(test_convert_agent.TestConvertAgent):
  """
  Agent used to convert test base class, generate TestCommon and TestRule file
  """
  @classmethod
  def ignore_files(cls):
    return ['chrome/test/android/javatests/src/org/chromium/chrome/test/\
        ChromeActivityTestCaseBase.java']

  @classmethod
  def filename_match(cls, whole_path):
    if whole_path.endswith('TestBase.java'):
      return True
    if whole_path.endswith('TestCaseBase.java'):
      return True
    else:
      return False

  @staticmethod
  def class_runner():
    raise Exception("This should not be called")

  @staticmethod
  def raw_api_mapping():
    return {}

  def _object_to_string(self,element):
    return self.content[
        self._lexposToLoc(element.lexpos):self._lexposToLoc(element.lexend)+1]

  def _all_objects_to_string_list(self, elements):
    return [self._object_to_string(e) for e in elements]

  def getPackage(self):
    return self.element_table[model.PackageDeclaration][0].name.value

  def implementsTestCommonCallback(self, common_callback_class_name):
    self._replaceString(
        r'(^public.*?){', r'\1implements %s {' % common_callback_class_name,
        element=self.main_class)

  def createGetter(self, field):
    try:
      variable_name = field.variable_declarators[0].variable.name
      if variable_name.startswith('m'):
        method_name = variable_name[1:]
      elif '_' in variable_name:
       method_name = ''.join([x.capitalize() for x in variable_name.split('_')])

      return_type = field.type.name.value
      method = 'public %s get%s() {\n        return mTestCommon.%s;\n    }' % (
          return_type, method_name, variable_name)
      assert isinstance(field, model.FieldDeclaration)
      first_method = self.main_element_table[model.MethodDeclaration][0]
      self._insertAbove(first_method, method)
    except Exception:
      self.logger.warn('Failed to create getter for %s', field)

  def removeAndReturnStaticFields(self):
    field_list = self.main_element_table.get(model.FieldDeclaration, [])
    (static_accessible, static_inaccessible, member_accessible,
        member_inaccessible) = ([], [], [], [])
    for i in field_list:
      if 'public' in i.modifiers or 'protected' in i.modifiers:
        self.createGetter(i)
        if 'static' in i.modifiers:
          static_accessible.append(self._removeElement(i))
        else:
          member_accessible.append(self._removeElement(i))
      else:
        if 'static' in i.modifiers:
          static_inaccessible.append(self._removeElement(i))
        else:
          member_inaccessible.append(self._removeElement(i))
    return (member_accessible, member_inaccessible, static_accessible,
            static_inaccessible)

  def _methodUnderBlock(self, m):
    block_range = []
    for b in self.main_element_table[model.Block]:
      block_range.append((b.lexpos, b.lexend))
    for r in block_range:
      if m.lexpos > r[0] and m.lexend < r[1]:
        return True
    return False

  def getMethods(self):
    accessible, inaccessible = [], []
    for m in self.actionOnMethodDeclaration(
        condition=lambda x:'\n' == self.content[self._lexposToLoc(x.lexpos-5)]):
      if 'public' in m.modifiers or 'protected' in m.modifiers:
        accessible.append(m)
      else:
        inaccessible.append(m)
    return accessible, inaccessible

  def removeElements(self, elements):
    for i in elements:
      self._removeElement(i)

  def getElementContent(self, elements):
    content = []
    for m in elements:
      content.append(self._object_to_string(m))
    return content

  def CommonizeAndRemoveMethods(self, methods):
    for m in methods:
      arg = '()'
      if m.parameters:
        arg = '(%s)' % ', '.join([p.variable.name for p in m.parameters])
      self._replaceString(
          r'(.*?) {.*}',
          r'\1 {\n        mTestCommon.%s%s;\n    }' % (m.name, arg),
          element=m, flags=re.DOTALL)

  def actions(self):
    self.changeAssertions()
    self.SaveAndReload()
    package = self.getPackage()

    # Get dirname and file names for test common and test rule
    dirname = '/'.join(self._filepath.split('/')[:-1])
    filename = self._filepath.split('/')[-1]
    prefix = re.match(r'(.*)Test.*\.java', filename).group(1)
    test_common_class_name = prefix+'TestCommon'
    test_common_callback_class_name = test_common_class_name+'Callback'
    test_rule_class_name = prefix+'TestRule'

    self.implementsTestCommonCallback(test_common_class_name)

    (_, inaccessible_member_fields, accessible_static_fields,
        inaccessible_static_fields) = self.removeAndReturnStaticFields()

    accessible_methods, inaccessible_methods = self.getMethods()
    accessible_methods_content_list = self.getElementContent(accessible_methods)
    inaccessible_method_content_list = self.getElementContent(
        inaccessible_methods)
    class_list = self.actionOnX(model.ClassDeclaration, main_table=False,
        condition=lambda x: not x == self.main_class)
    class_content_list = self.getElementContent(class_list)
    self.removeElements(inaccessible_methods)
    self.removeElements(class_list)

    self.CommonizeAndRemoveMethods(accessible_methods)
    self.SaveAndReload()
    commonized_methods, _ = self.getMethods()

    imports = self.actionOnX(model.ImportDeclaration, main_table=False)

    test_common_dict = {
        'classname': test_common_class_name,
        'package': package,
        'imports': self._all_objects_to_string_list(imports),
        'classes': class_content_list,
        'fields': inaccessible_static_fields+inaccessible_member_fields,
        'methods': inaccessible_method_content_list\
            + accessible_methods_content_list,
        'common_callback': test_common_callback_class_name,
    }

    test_rule_dict = {
        'classname': test_rule_class_name,
        'package': package,
        'imports': self._all_objects_to_string_list(imports),
        'fields': accessible_static_fields,
        'methods': self._all_objects_to_string_list(commonized_methods),
        'testcommon': test_common_class_name,
        'common_callback': test_common_callback_class_name,
    }

    self.generateClass(_TEST_COMMON_JINJA_TEMPLATE, test_common_dict,
                       os.path.join(dirname, test_common_class_name+'.java'))
    self.generateClass(_TEST_RULE_JINJA_TEMPLATE, test_rule_dict,
                       os.path.join(dirname, test_rule_class_name+'.java'))
    test_rule_agent = base_agent.BaseAgent(
        self.parser, os.path.join(dirname, test_rule_class_name+'.java'))
    test_rule_agent.actionOnMethodDeclaration(
        action=lambda x: test_rule_agent._replaceString(
            'protected', 'public', element=x))
    self.Save()
    test_rule_agent.Save()

  def generateClass(self, template_string, data, filepath):
    with codecs.open(filepath, encoding='utf-8', mode='w') as f:
      f.write(jinja2.Template(template_string).render(data))

  def skip(self):
    return False



