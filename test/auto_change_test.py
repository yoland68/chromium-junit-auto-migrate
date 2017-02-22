#!/usr/bin/env python

import plyj.parser as ply
import plyj.model as model
import plyj.auto_change as auto_change

import logging
import unittest
from mock import patch

class MockTest(unittest.TestCase):
  @patch(
      'plyj.auto_change.TraverseTree',
      lambda x: (
          [model.SourceElement(lexpos=3), model.SourceElement(lexpos=8)],
          {}, {}, {}))
  def testInsertAbove(self):
    jft = auto_change.JavaFileTree(None, None, None, content='\nabcd efg\n')
    element = jft._element_list[0]
    jft._insertAbove(element, '1234')
    self.assertEqual(jft.content, '\n1234\nabcd efg\n')

  @patch(
      'plyj.auto_change.TraverseTree',
      lambda x: (
          [model.SourceElement(lexpos=3), model.SourceElement(lexpos=8)],
          {}, {}, {}))
  def testInsertAbove2(self):
    jft = auto_change.JavaFileTree(None, None, None, content='\nabcd efg\n')
    element = jft._element_list[1]
    jft._insertAbove(element, '1234')
    self.assertEqual(jft.content, '\n1234\nabcd efg\n')

  @patch(
      'plyj.auto_change.TraverseTree',
      lambda x: (
          [model.SourceElement(lexpos=3), model.SourceElement(lexpos=8)],
          {}, {}, {}))
  def testInsertBelow(self):
    jft = auto_change.JavaFileTree(None, None, None, content='\nabcd efg\n')
    element = jft._element_list[0]
    jft._insertBelow(element, '1234')
    self.assertEqual(jft.content, '\nabcd efg\n1234\n')

  @patch(
      'plyj.auto_change.TraverseTree',
      lambda x: (
          [model.SourceElement(lexpos=3), model.SourceElement(lexpos=8)],
          {}, {}, {}))
  def testInsertAboveThenBelow(self):
    jft = auto_change.JavaFileTree(None, None, None, content='\nabcd efg\n')
    element = jft._element_list[0]
    jft._insertAbove(element, '1234')
    jft._insertBelow(element, '1234')
    self.assertEqual(jft.content, '\n1234\nabcd efg\n1234\n')

  @patch(
      'plyj.auto_change.TraverseTree',
      lambda x: (
          [model.SourceElement(lexpos=3), model.SourceElement(lexpos=8),
           model.SourceElement(lexpos=12)], {}, {}, {}))
  def testInsertBelowThenAbove(self):
    jft = auto_change.JavaFileTree(None, None, None, content='\nabcd efg\nxyz')
    element = jft._element_list[1]
    jft._insertBelow(element, '1234')
    element = jft._element_list[2]
    jft._insertAbove(element, '1234')
    self.assertEqual(jft.content, '\nabcd efg\n1234\n1234\nxyz')

  @patch(
      'plyj.auto_change.TraverseTree',
      lambda x: (
          [model.SourceElement(lexpos=3, lexspan=(3,6)),
           model.SourceElement(lexpos=8, lexspan=(8,10)),
           model.SourceElement(lexpos=12, lexspan=(12,14))], {}, {}, {}))
  def testReplaceString(self):
    jft = auto_change.JavaFileTree(None, None, None, content='\nabcd efg\nxyz')
    element = jft._element_list[0]
    jft._replaceString('bc\w', '1', element=element)
    self.assertEqual(jft.content, '\na1 efg\nxyz')
    element = jft._element_list[1]
    jft._replaceString('\w\wg', '', element=element, optional=False)
    self.assertEqual(jft.content, '\na1 \nxyz')
    element = jft._element_list[2]
    jft._replaceString('xyz1', '', element=element, optional=True)
    self.assertEqual(jft.content, '\na1 \nxyz')
    jft._replaceString('xyz', 'xxx', element=element, optional=True)
    self.assertEqual(jft.content, '\na1 \nxxx')

class Test(unittest.TestCase):
  def setUp(self):
    self.test_string ='''     @Override
      protected void setUp() throws Exception {
          super.setUp();
          mTestController = new TestController();
          injectObjectAndReload(mTestController, "testController");
      }'''

  def testHelperReturnReplacement(self):
    pattern = ' protected '
    replacement = ' public '
    expected_result = '''     @Override
      public void setUp() throws Exception {
          super.setUp();
          mTestController = new TestController();
          injectObjectAndReload(mTestController, "testController");
      }'''
    self.assertEqual(
        expected_result, auto_change._ReturnReplacement(
            pattern, replacement, self.test_string))

  def testHelperReturnReplacementRemove(self):
    pattern = ' *@Override'
    replacement = ''
    expected_result = '''
      protected void setUp() throws Exception {
          super.setUp();
          mTestController = new TestController();
          injectObjectAndReload(mTestController, "testController");
      }'''

    self.assertEqual(
        expected_result, auto_change._ReturnReplacement(
            pattern, replacement, self.test_string))


class InstrumentationTestCaseApiReplacementTest(unittest.TestCase):
  def testNormal(self):
    file_string = '''package test_junit4_autochange;

import a.b.c;

public class Test {

  public static void main(String[] args) {
    System.out.println("hello");
    getInstrumentation().doSomething();
    myOwnObject.getInstrumentation();
  }

  @Annotation
  public void test() {
    lalala();
    getInstrumentation().doSomething();
    myOwnObject.getInstrumentation();
  }
}'''
    expected_string = '''package test_junit4_autochange;

import a.b.c;
import android.support.test.InstrumentationRegistry;

public class Test {

  public static void main(String[] args) {
    System.out.println("hello");
    InstrumentationRegistry.getInstrumentation().doSomething();
    myOwnObject.getInstrumentation();
  }

  @Annotation
  public void test() {
    lalala();
    InstrumentationRegistry.getInstrumentation().doSomething();
    myOwnObject.getInstrumentation();
  }
}'''
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    java_parser = ply.Parser(logger)
    tree = java_parser.parse_string(file_string)
    file_tree = auto_change.JavaFileTree(tree, None, None, content=file_string)
    file_tree.replaceInstrumentationApis()
    self.assertEqual(file_tree.content, expected_string)


class SimpleFileTest(unittest.TestCase):
  def setUp(self):
    file_string = '''package test_junit4_autochange;

import a.b.c;
import org.junit.TestCase;

public class Test extends TestCase {

  public static void main(String[] args) {
    System.out.println("hello");
    getInstrumentation().doSomething();
    myOwnObject.getInstrumentation();
  }

  @Annotation
  protected void setUp() {
    super.setUp();
    lalala();
  }

  @Annotation
  protected void tearDown() {
    lalala();
    super.tearDown();
    getInstrumentation().doSomething();
    myOwnObject.getInstrumentation();
  }
}'''
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    java_parser = ply.Parser(logger)
    tree = java_parser.parse_string(file_string)
    self.file_tree = auto_change.JavaFileTree(
        tree, None, {'TestCase':{'method':{'A':'A'}}}, content=file_string)

  def testHelperFindNextElementIndex(self):
    expected_file_string = '''package test_junit4_autochange;

import a.b.c;
import org.junit.TestCase;
import org.junit.After;
import org.junit.Before;

public class Test extends TestCase {

  public static void main(String[] args) {
    System.out.println("hello");
    getInstrumentation().doSomething();
    myOwnObject.getInstrumentation();
  }

  @Before
  @Annotation
  public void setUp() {
    lalala();
  }

  @After
  @Annotation
  public void tearDown() {
    lalala();
    getInstrumentation().doSomething();
    myOwnObject.getInstrumentation();
  }
}'''
    # ipdb.set_trace()
    self.file_tree.changeSetUp()
    self.assertEqual(self.file_tree.content, expected_file_string)

  def testAddClassRunner(self):
    expected_file_string = '''package test_junit4_autochange;

import a.b.c;
import org.junit.TestCase;
import org.chromium.base.test.BaseJUnit4ClassRunner;
import org.junit.runner.RunWith;

@RunWith(BaseJUnit4ClassRunner.class)
public class Test extends TestCase {

  public static void main(String[] args) {
    System.out.println("hello");
    getInstrumentation().doSomething();
    myOwnObject.getInstrumentation();
  }

  @Annotation
  protected void setUp() {
    super.setUp();
    lalala();
  }

  @Annotation
  protected void tearDown() {
    lalala();
    super.tearDown();
    getInstrumentation().doSomething();
    myOwnObject.getInstrumentation();
  }
}'''
    # ipdb.set_trace()
    self.file_tree.addClassRunner()
    # DebugTest(self.file_tree.content, expected_file_string)
    self.assertEqual(self.file_tree.content, expected_file_string)

  def testRemoveExtends(self):
    expected_file_string='''package test_junit4_autochange;

import a.b.c;


public class Test {

  public static void main(String[] args) {
    System.out.println("hello");
    getInstrumentation().doSomething();
    myOwnObject.getInstrumentation();
  }

  @Annotation
  protected void setUp() {
    super.setUp();
    lalala();
  }

  @Annotation
  protected void tearDown() {
    lalala();
    super.tearDown();
    getInstrumentation().doSomething();
    myOwnObject.getInstrumentation();
  }
}'''
    self.file_tree.removeExtends()
    self.assertEqual(self.file_tree.super_class_name, 'TestCase')
    self.assertEqual(self.file_tree.content, expected_file_string)

class InsertActivityTestRuleTest(unittest.TestCase):
  def testOneLinePackageDelaclaration(self):
    file_string = '''package test_junit4_autochange;

import a.b.c;

public class Test {

    public static void main(String[] args) {
      System.out.println("hello");
    }
}'''

    expected_string = '''package test_junit4_autochange;

import a.b.c;
import org.junit.Rule;

public class Test {

    @Rule
    public ActivityTestRule<TestActivity> mActivityTestRule = new ActivityTestRule<>();

    public static void main(String[] args) {
      System.out.println("hello");
    }
}'''
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    java_parser = ply.Parser(logger)
    tree = java_parser.parse_string(file_string)
    file_tree = auto_change.JavaFileTree(tree, None, None, file_string)
    file_tree._insertActivityTestRule(
        'ActivityTestRule<TestActivity>', 'ActivityTestRule<>()')
    self.assertEqual(file_tree.content, expected_string)

  def testTwoLinePackageDelaration(self):
    file_string = '''package test_junit4_autochange;

import a.b.c;

public class Test extends
    lalalalalal {

    public static void main(String[] args) {
      System.out.println("hello");
    }
}'''

    expected_string = '''package test_junit4_autochange;

import a.b.c;
import org.junit.Rule;

public class Test extends
    lalalalalal {

    @Rule
    public ActivityTestRule<TestActivity> mActivityTestRule = new ActivityTestRule<>();

    public static void main(String[] args) {
      System.out.println("hello");
    }
}'''
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    java_parser = ply.Parser(logger)
    tree = java_parser.parse_string(file_string)
    file_tree = auto_change.JavaFileTree(
        tree, None, {'lalalalalal': {'method':{'A':'A'}}}, content=file_string)

    file_tree._insertActivityTestRule(
        'ActivityTestRule<TestActivity>', 'ActivityTestRule<>()')
    # DebugTest(file_tree.content, expected_string)
    self.assertEqual(file_tree.content, expected_string)

class AssertionTest(unittest.TestCase):
  def setUp(self):
    file_string = '''package test_junit4_autochange;

import a.b.c;

public class Test {

  public static void main(String[] args) {
    System.out.println("hello");
  }

  @SmallTest
  @Feature({"Navigation"})
  public void testDefaultCreateState() throws Exception {
      assertEquals(View.INVISIBLE, mPopupZoomer.getVisibility());
      assertFalse(mPopupZoomer.isShowing());
  }

  @SmallTest
  @Feature({"Navigation"})
  public void testShowWithoutBitmap() throws Exception {
      mPopupZoomer.show(new Rect(0, 0, 5, 5));

      // The view should be invisible.
      assertEquals(View.INVISIBLE, mPopupZoomer.getVisibility());
      assertFalse(mPopupZoomer.isShowing());
      fail("abcde");
  }

  @SmallTest
  @Feature({"Navigation"})
  public void testShowWithBitmap() throws Exception {
      mPopupZoomer.setBitmap(Bitmap.createBitmap(10, 10, Bitmap.Config.ALPHA_8));
      mPopupZoomer.show(new Rect(0, 0, 5, 5));
      abc(assertNotNull(X));
      Runnable r = new Runnable() {
          @Override
          public void run() {
            assertSame(x, y);
          }
      };

      // The view should become visible.
      assertEquals(View.VISIBLE, mPopupZoomer.getVisibility());
      assertTrue(mPopupZoomer.isShowing());
  }
}'''
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    java_parser = ply.Parser(logger)
    tree = java_parser.parse_string(file_string)
    self.file_tree = auto_change.JavaFileTree(
        tree, None, None, content=file_string)

  def testAddTestAnnotation(self):
    expected_file_string = '''package test_junit4_autochange;

import a.b.c;
import org.junit.Test;

public class Test {

  public static void main(String[] args) {
    System.out.println("hello");
  }

  @Test
  @SmallTest
  @Feature({"Navigation"})
  public void testDefaultCreateState() throws Exception {
      assertEquals(View.INVISIBLE, mPopupZoomer.getVisibility());
      assertFalse(mPopupZoomer.isShowing());
  }

  @Test
  @SmallTest
  @Feature({"Navigation"})
  public void testShowWithoutBitmap() throws Exception {
      mPopupZoomer.show(new Rect(0, 0, 5, 5));

      // The view should be invisible.
      assertEquals(View.INVISIBLE, mPopupZoomer.getVisibility());
      assertFalse(mPopupZoomer.isShowing());
      fail("abcde");
  }

  @Test
  @SmallTest
  @Feature({"Navigation"})
  public void testShowWithBitmap() throws Exception {
      mPopupZoomer.setBitmap(Bitmap.createBitmap(10, 10, Bitmap.Config.ALPHA_8));
      mPopupZoomer.show(new Rect(0, 0, 5, 5));
      abc(assertNotNull(X));
      Runnable r = new Runnable() {
          @Override
          public void run() {
            assertSame(x, y);
          }
      };

      // The view should become visible.
      assertEquals(View.VISIBLE, mPopupZoomer.getVisibility());
      assertTrue(mPopupZoomer.isShowing());
  }
}'''
    self.file_tree.addTestAnnotation()
    self.assertEqual(self.file_tree.content, expected_file_string)

  def testChangeAssertions(self):
    expected_file_string = '''package test_junit4_autochange;

import a.b.c;
import org.junit.Assert;

public class Test {

  public static void main(String[] args) {
    System.out.println("hello");
  }

  @SmallTest
  @Feature({"Navigation"})
  public void testDefaultCreateState() throws Exception {
      Assert.assertEquals(View.INVISIBLE, mPopupZoomer.getVisibility());
      Assert.assertFalse(mPopupZoomer.isShowing());
  }

  @SmallTest
  @Feature({"Navigation"})
  public void testShowWithoutBitmap() throws Exception {
      mPopupZoomer.show(new Rect(0, 0, 5, 5));

      // The view should be invisible.
      Assert.assertEquals(View.INVISIBLE, mPopupZoomer.getVisibility());
      Assert.assertFalse(mPopupZoomer.isShowing());
      Assert.fail("abcde");
  }

  @SmallTest
  @Feature({"Navigation"})
  public void testShowWithBitmap() throws Exception {
      mPopupZoomer.setBitmap(Bitmap.createBitmap(10, 10, Bitmap.Config.ALPHA_8));
      mPopupZoomer.show(new Rect(0, 0, 5, 5));
      abc(Assert.assertNotNull(X));
      Runnable r = new Runnable() {
          @Override
          public void run() {
            Assert.assertSame(x, y);
          }
      };

      // The view should become visible.
      Assert.assertEquals(View.VISIBLE, mPopupZoomer.getVisibility());
      Assert.assertTrue(mPopupZoomer.isShowing());
  }
}'''
    # ipdb.set_trace()
    self.file_tree.changeAssertions()
    self.assertEqual(self.file_tree.content, expected_file_string)

def DebugTest(expected_string, actual_string):
  with open('/usr/local/google/home/yolandyan/Desktop/expected.java', 'w') as expected, \
        open('/usr/local/google/home/yolandyan/Desktop/actual.java', 'w') as actual:
    expected.write(expected_string)
    actual.write(actual_string)


