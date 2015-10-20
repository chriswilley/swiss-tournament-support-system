# Swiss Tournament Support System

Using this tool you can manage your own ["swiss-system" tournament](https://en.wikipedia.org/wiki/Swiss-system_tournament) for activities like chess, Magic: The Gathering, Scrabble, or other games. Much easier than pencil and paper!


## Table of contents

* [Program installation](#installation)
* [Database setup](#database-setup)
* [Testing the tournament functions](#testing-the-tournament-functions)
* [Creator](#creator)
* [Copyright and license](#copyright-and-license)


## Installation

For starters, you need [Python](https://www.python.org/downloads/). The program was written for Python 2.7, so that's what you should download and install. You may already have Python, especially if you're on a Mac or Linux machine. To check, open a Terminal window (on a Mac, use the Spotlight search and type in "Terminal"; on a PC go to Start > Run and type in "cmd") and type "python" at the prompt. You should get something that looks like this (run on my Mac):

```
Python 2.7.10 (v2.7.10:15c95b7d81dc, May 23 2015, 09:33:12)
[GCC 4.2.1 (Apple Inc. build 5666) (dot 3)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

Note the version number (2.7.10 in this case). If it starts with "3.", you should download version 2.7. If you have questions about any of this, check Python's [excellent online documentation](https://www.python.org/doc/).

The program requires PostgreSQL as a database server, which you can [download here](http://www.postgresql.org/download/). PostgreSQL is an awesome (and free!) database server that's extremely powerful. There are also lots of tutorials and other articles about it all over the Web.

Finally, you'll need [git](http://git-scm.com/download) so that you can clone this project.


## Database setup

With PostgreSQL installed, you can easily setup the tournament database in a Terminal window. Just navigate to the folder that was created when you cloned the project, and type:

```
psql
```

This will put you in the PostgreSQL shell environment. Your prompt will look like this: '=>', and you'll see a message similar to:

```
psql (9.3.9)
Type "help" for help.
```

Now you can execute SQL commands and do all kinds of other neat stuff. But for now, just type:

```
\i tournament.sql
```

This will import the .sql file you cloned, which sets up the database completely. That was easy. To exit the PostgreSQL shell, just hit Ctrl-D.


## Testing the tournament functions

Once you have the project files and the database is set up, go to a command prompt and type:

```
python tournament_test.py
```

For now, this is the only interface to the program. All tests should pass.


## Creator

This program was built by me, Chris Willey, as part of the Udacity Nanodegree program for [Full Stack Developer](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).


## Copyright and License

Code and documentation copyright 2015 Christopher Willey. Code released under the MIT license.