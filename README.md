# Chromium JUnit4 Auto Change Script
The purpose of this script is to help tokenize and parse instrumentation
javatests that were based in JUNit3 and automatically refactor them to JUnit4
style javatests.

The script is based on [PLY](www.dabeaz.com/ply/) (a lex/yacc implementation
in python) and [PLYJ](https://github.com/musiKk/plyj/) (Java 7 parser written in Python based on ply)

#Usage
Run the following

    pip install ply
    git clone https://github.com/yoland68/chromium-junit-auto-migrate.git "$CLANKIUM_SRC"/autochange
    cd "$CLANKIUM_SRC"
    python autochange/autochange/auto_change.py -d [Directory] -m [MAPPING_JSON]

`[Directory]` is which directory to convert, `[MAPPING_JSON]` is the path to
a json file that maps TestBase classes to TestRules (for detail of how JUnit4 is different from JUnit3, check [TBA]())

If `[MAPPING_JSON]` is not provided, the script would only be able to change any tests that extends from InstrumentationTestCase.

#How it works
The script would find all the java file that are named `*Test.java`

It tokenizes and parses them so it would be easy to search for java code by its type (e.g. find all methods invocation that are named `XYZ` that are not declared locally), 

It finds the API calls, annotations, class declaration and other componenets that are associated to the migration and make the change

#Caveats
There are a couple of things this script **can not** do for you

1. Auto convert tests that rely on test thread to have message handler (Error message: `java.lang.RuntimeException: Can't create handler inside thread that has not called Looper.prepare()`). This is because AndroidJUnitRunner prevents any Handler from being created on the Instrumentation worker thread. In terms solution, one should try running whatever parts that causes these runtime errors on UI thread. Check this issue for more detail on AndroidJUnitRunner Handler issue: [link](https://github.com/skyisle/android-test-kit/issues/121)
2. assertEquals(float a, float b), this is deprecated in JUnit4 Assert library, and it is replaced by assertEquals(float a, float b, double delta). This script does not auto change this API because no default delta value is provided. **Beware that despite Assert.assertEquals(float a, float b) is only deprecated, in android instrumentation tests, it will fail the assertion!** For more on this issue: [link](http://junit.org/junit4/javadoc/latest/org/junit/Assert.html)
3. Changed if any of the changed API now throws different Exceptions, the script is not powerful enough to change that
4. Import order and file format. There are various file formating problem and package import order problems when using the auto change script. The best thing to do is to use Eclipse to format the code and organize import for you.
5. These methods that doesn't get automatically convert: sentKeys(String s), sendKeys(int... keys), sendRepeatedKeys(int...keys) ([link](https://developer.android.com/reference/android/test/InstrumentationTestCase.html))
6. Inherited public variables. Issue: TestBase has a public variable, and child test access that variable), Solution: Because the TestBase is mostly 1 to 1 mapped to TestRule class, one 


#Bug
please email +yolandyan about any of the bug you've encounted or create issue in this repo
