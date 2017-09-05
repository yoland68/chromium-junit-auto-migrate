# Chromium JUnit4 Auto Change Script
The purpose of this script is to help tokenize and parse Chromium instrumentation
javatests that were based in JUnit3 and automatically refactor them to JUnit4
style javatests.

The script is based on [PLY](http://www.dabeaz.com/ply/) (a lex/yacc implementation
in python) and [PLYJ](https://github.com/musiKk/plyj/) (Java 7 parser written in Python based on ply)

## Usage

Run the following

    pip install ply
    git clone https://github.com/yoland68/chromium-junit-auto-migrate.git "$CLANKIUM_SRC"/autochange
    cd "$CLANKIUM_SRC"
    python autochange/src/auto_change.py [option-arguments]

optional arguments:
```text
  -h, --help            show this help message and exit
  -u, --use-base-class  Use another base class to convert
  -f JAVA_FILE, --java-file JAVA_FILE
                        Java file
  -d DIRECTORY, --directory DIRECTORY
                        Directory where all java file lives
  -v, --verbose         Log info
  -l, --list-agents     List all available agents
  -n, --save-as-new     Save as a new file
  -a AGENT, --agent AGENT
                        Specify the agent for the current file
```

Example: converting PaymentRequestDataUrlTest.java to JUnit 4 would be
```
python autochange/src/auto_change.py -f chrome/android/javatests/src/org/chromium/chrome/browser/payments/PaymentRequestDataUrlTest.java -a payment-test
```
or simply without agent specification
```
python autochange/src/auto_change.py -f chrome/android/javatests/src/org/chromium/chrome/browser/payments/PaymentRequestDataUrlTest.java
```

`[Directory]` is which directory to convert 


## Actions For Normal Test.java

Test with different parents tend to have different convertion actions, but normally, a test convertion would include the following actions

1. **Remove extends**: remove inheritance in tests and imported packages
- **Change setUp**: add @Before annotation to `setUp()`, change it to public (required by BlockJUnit4ClassRunner), remove `super.setUp()` call
- **Change Assertions**: find all the assertion calls and change them to use new [Assert class](http://junit.org/junit4/javadoc/latest/org/junit/Assert.html)
- **Replace instrumentation calls**: replace `getInstrumentation()` with `InstrumentationRegistry.getInstrumentation()`, `getContent()` with `InstrumentationRegistry.getInstrumentation()`.
- **Add `@RunWith(CustomClassRunner.class)`** and import the package
- **Add `@Test`** to every test method
- **Insert TestRule** or ActivityTestRule at the beginning of the test file (e.g. `@Rule public MyTestRule mRule = new MyTestRule();`)
- **Change `runTestOnUiThread(Runnable r)`** to `mActivityTestRule.runOnUiThread()`
- **Import any inherited** classes, annotations, interfaces
- **Change API calls** based on the parent's declared APIs (e.g. XTestBase.java is refactored to be XActivityTestRule.java, any parent method call, such as`methodX()`, in javatests that extends from XTestBase would be refactored to `mActivityTestRule.methodX()`

See this [link](https://github.com/yoland68/chromium-junit-auto-migrate/blob/master/src/chrome_convert_agents.py#L408) for action definitions

## How it works
The script would find all the java file that are named `*Test.java` in a given directory

It tokenizes and parses the java file so it would be easy to search for java code by its type (e.g. find all methods invocation that are named `XYZ` that are not declared locally), 

It finds the API calls, annotations, class declaration and other componenets that are associated to the migration and make the change

## Success rate

For `src/content` ([CL](https://codereview.chromium.org/2708243004)), I was able to auto change 45 test files out of 50 without compiling errors (the manual fix for that is minimal)
After a few min manual fix, when running these tests, 387 out of 429 test methods passes (90.2%), 36 out of 50 test files passes (72%)

For `src/base/javatests`, 100% test was able to compile after script run, 22 out of 25 tests runs successfully (88%)


## Known issues
There are a couple of things this script **can not** do for you

0. **TEST WILL NOT JUST WORK AFTER AUTO CONVERT, PLEASE TRY COMPILING AND RUNNING THEM FIRST**
1. Auto convert tests that rely on test thread to have message handler will not work (Example error message: `java.lang.RuntimeException: Can't create handler inside thread that has not called Looper.prepare()`). This is because AndroidJUnitRunner prevents any Handler from being created on the Instrumentation worker thread. In terms solution, one should try to run whatever parts that causes these runtime errors UI thread. Check this issue for more detail on AndroidJUnitRunner Handler issue: [link](https://github.com/skyisle/android-test-kit/issues/121)

2. [`assertEquals(float a, float b)`](http://junit.org/junit4/javadoc/latest/org/junit/Assert.html), this is deprecated in JUnit4 Assert class, and it is replaced by assertEquals(float a, float b, double delta). This script does not auto change this API because no default delta value is provided. **Beware that despite Assert.assertEquals(float a, float b) is only deprecated, when running in android instrumentation tests, it will fail the assertion no matter what!**

3. Changed if any of the changed API now throws different Exceptions, the script is not powerful enough to change that

4. Import order and file format. There are various file formating problem and package import order problems when using the auto change script. The best thing to do is to use Eclipse to format the code and organize import for you.

5. Inherited public variables. Issue: TestBase class has a public variable, and child tests access that variable. Now that TestBases are gone. Solution: Because the TestBase's APIs are mostly 1 to 1 mapped to TestRule class, one should create a getter for these public variable in TestRule.

6. Java 7 only, recently a lot of tests have been converted to Java8 syntax, one way to get around it is to comment out the java8 syntax like lambdas


## Bug
please email +yolandyan about any of the bug you've encounted or create issue in this repo
