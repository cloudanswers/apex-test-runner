apex-test-runner
----------------

this is my work-in-progress test runner to make developing apex
using test driven development a little bit easier than having
to wait for eclipse to constantly figure out how not to freeze




concept
-------

overview:

1.  you start up the test runner
2.  test runner runs all your tests to see if any fail
3.  when you update files in the local filesystem, only the failed tests run
4.  once your failing tests run, all tests are run again, if broken goto: 3
5.  you make some improvement in a non-test class
6.  test watcher runs all test classes that refer to your class name
    (this may not be smart enough, but it is a good start)
7.  if you edit a virtual class, all extending classes are automatically
    recompiled so you know if you broke something without having to
    run your unit tests

TODO
----

1. find all test classes and run all tests
2. monitor fsevents for file changes to know what test to run
3. function to find related tests to a class

