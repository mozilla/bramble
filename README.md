Bramble
=======

A dashboard for the Mozilla [Briar Patch][bp] focused on the overall health
of the Mozilla build farm.

API
---
```
/builds
returns all known build uids

request params:
    date -    restrict result to builds on a particular day (optional)
               format YYYY-MM-DD
    hour -    restrict to builds in a particular hour (optional)
               format HH, valid iff the date is provided
    changes - if true, restrict to builds with source changes
               (optional), valid iff date or date and time provided

example:
    http://127.0.0.1:8000/builds/?date=2012-03-22 ->
    [{"type": "build", "uid": "e94042e9b58a40b7841dfd05fdde72da"},
     {"type": "build", "uid": "f07a73a9d5cd466c86b4e1078abcfb25"},
     {"type": "build", "uid": "78214761f24644199b7bcd02dc97f976"},
     {"type": "build", "uid": "363da5c3e3954e77a8d6fbd6b788e81c"}]
```
```
/builds/:uid/jobs
returns a list of jobs spawned by a specific build

:uid - 32 alphanumeric digit build uid

example
    http://127.0.0.1:8000/builds/e94042e9b58a40b7841dfd05fdde72da/jobs ->
    [{"master": "buildbot-master19", "type": "job",
      "uid": "e94042e9b58a40b7841dfd05fdde72da", "build_number": "17"},
     {"master": "buildbot-master16", "type": "job",
      "uid": "e94042e9b58a40b7841dfd05fdde72da", "build_number": "19"},
     {"master": "buildbot-master16", "type": "job",
      "uid": "e94042e9b58a40b7841dfd05fdde72da", "build_number": "14"}]
```
```
/build/:uid/changeset
returns the changeset information for a particular build uid

:uid - 32 alphanumeric digit build uid

example
    http://127.0.0.1:8000/builds/e94042e9b58a40b7841dfd05fdde72da/changeset ->
    {"pgo_build": "False",
     "comments": "Bug 732976 - SingleSourceFactory should generate checksums file. r=ted, a=lsblakk",
     "project": "", "master": "buildbot-master10",
     "branch": "mozilla-esr10-macosx64-opt-unittest",
     "builduid": "e94042e9b58a40b7841dfd05fdde72da", "revision": "6c61683ed9cb"}
```
```
/machines/events/:event_type/
returns machine events with frequency counts

:event_type - restrict results to events of this type
              one of 'connect', 'disconnect', 'build'

example
    http://127.0.0.1:8000/machines/events/build/ ->
    [{"count": "1", "machine_name": "slave.talos-r3-fed-024_5", "type": "machine",
      "event": "build:finished"},
     {"count": "1", "machine_name": "slave.talos-r3-fed-024_1", "type": "machine",
      "event": "build:finished"},
     {"count": "1", "machine_name": "slave.linux64-ix-slave23_1", "type": "machine",
      "event": "build:finished"}]
```
```
/jobs/:uid/:master/:buildnumber/
returns all information about a job, pulled from the Pulse stream

:uid          - the build uid for the job
:master       - the master managing the jobs
:build_number - the build number

example:
    http://127.0.0.1:8000/jobs/e94042e9b58a40b7841dfd05fdde72da/buildbot-master18/1/ ->
    {"started": "2012-03-22T07:09:50+01:00",
     "product": "firefox",
     "who": "sendchange-unittest",
     "slave": "talos-r3-fed64-021",
     "branch": "mozilla-esr10",
     "log_url": "http://ftp.mozilla.org/pub/mozilla.org/firefox/tinderbox-builds/mozilla-esr10-linux64-debug/1332422842/mozilla-esr10_fedora64-debug_test-mochitests-1-bm18-tests1-linux-build1.txt.gz",
     "buildid": "20120322062722",
     "pgo_build": "False",
     "build_url": "http://ftp.mozilla.org/pub/mozilla.org/firefox/tinderbox-builds/mozilla-esr10-linux64-debug/1332422842/firefox-10.0.4esrpre.en-US.linux-x86_64.tar.bz2",
     "results": "0",
     "elapsed": "1164",
     "buildnumber": "1",
     "platform": "linux64",
     "finished": "2012-03-22T07:29:14+01:00",
     "statusdb_id": "10277667",
     "master": "buildbot-master18",
     "scheduler": "tests-mozilla-esr10-fedora64-debug-unittest",
     "builduid": "e94042e9b58a40b7841dfd05fdde72da",
     "revision": "6c61683ed9cb"}
```
[bp]: https://github.com/mozilla/briar-patch
