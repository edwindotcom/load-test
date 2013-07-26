Load test for jrconlin/pushgo. Runs types of tests:
* connect, hello, register, update, ack, close
* connect, hello, register, update, close
* connect, hello, register, update loop one channel, ack, close
* connect, hello, register, update loop different channel, ack, close
* connect, hello, ping loop, close

You can run this by installing Loads (mozilla-services/loads) and running this:
loads-runner load_gen.TestLoad.test_load -c 10 -u 10
