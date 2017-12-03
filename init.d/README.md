CasicsDB init.d files
=====================

We use these files on our CentOS 7-based system hosting our CasicsDB development database.  These are included for the sake of helping anyone else who may be attempting to get the system running, but please note that **you will need to modify `mongod` to suit your particular system**. Do not attempt to run these files as-is, because they are almost certainly not suitable for _your_ system.

* `mongod`: This file should be copied to `/etc/init.d/mongod`, and a symbolic link to `/etc/init.d/mongod` should be placed in `/etc/rcN.d`, where _N_ are usually `3` and `5` (but possibly others, depending on your particular system arrangements).  The contents should be modified to suit your particular installation.

* `99-mongodb-nproc.conf`: This file should (optionally) be copied to `/etc/security/limits.d/99-mongodb-nproc.conf` on our CentOS system to get rid of some system limits that Mongo will otherwise complain about when it starts up.
