apex-test-runner
----------------

this is my work-in-progress test runner to make developing apex
using test driven development a little bit easier than having
to wait for eclipse to constantly figure out how not to freeze


how to use
----------

    $ vi test.py # put in your credentials
    $ virtualenv venv
    $ pip install -r requirements.txt
    $ python test.py
    $ python test.py "Test_Lead_Automate"
    Running tests matching "Test_Lead_Automate"
    709e00000002W1NAAU (1/1)
    $ 

 Optionally the script will take an argument to filter the tests:

    $ python test.py "Test_Lead_%"
    Running tests matching "Test_Lead_Automate"
    709e00000002W1NAAU (1/1)
    $
    

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


current status
--------------

It runs all your tests you selected and prints out errors if there were any.
It is WAY faster than running them in eclipse.
It doesn't lock eclipse when the tests run so you can keep typing other code while tests for the last function run.

TODO
----

1. take auth settings out of script
1. monitor fsevents for file changes to know what test to run?
1. monitor the ApexClass table for changes?
1. function to find related tests to a class so we're not blindly running all of them
