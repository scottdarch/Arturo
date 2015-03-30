![Arturo Logo](docs/ArturoLogo.png)

## Introducing Arturo

> A command-line tool for Arduino

This is a fork from [ino/master](https://github.com/amperka/ino/commit/f23ee5cb14edc30ec087d3eab7b301736da42362).
The original ino contributors did a fantastic job but they decided they no longer
had time to maintain this tool. I asked them if they wanted me to take over ino
but they preferred that I fork it. And so Arturo was born.

Stay tuned for more details and changes. I do plan on going through the existing
ino PRs and issues to see if there's anything I can fix.

I am looking for other contributors as well. I especially need Windows and Linux
testers as I'm doing all this work on a mac.

## Installing Arturo

Clone this repo, cd Arturo, make install.

Remember that the Arturo command is ```ano```. It should not conflict in any way
with ino and you can install the two side-by-side (please file any issues if this
is not true).

Make sure you do an ```ano clean``` if you had previously built using ino. I will
try to handle this automatically in a future release.
