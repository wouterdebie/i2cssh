# i2cssh

i2cssh is a csshX (http://code.google.com/p/csshx/) like tool for connecting over ssh to multiple machines. But instead of creating separate windows and having
a master window for input, i2cssh uses iterm2 split panes and "Send input to all sessions" (cmd-shift-i) to send commands
to all sessions.

## Installing 

    $ gem install i2cssh

## Usage
    Usage: i2cssh [options]  [(username@host [username@host] | username@cluster)]
    -A, --forward-agent              Enable SSH agent forwarding
    -l, --login LOGIN                SSH login name
    -e, --environment KEY=VAL        Send environment vars (comma-separated list, need to start with LC_)
    -F, --fullscreen                 Make the window fullscreen
    -C, --columns COLUMNS            Number of columns (rows will be calculated)
    -R, --rows ROWS                  Number of rows (columns will be calculated)
    -b, --broadcast                  Start with broadcast input (DANGEROUS!)
    -nb, --nobroadcast               Disable broadcast
    -p, --profile PROFILE            Name of the iTerm2 profile (default: Default)
    -2, --iterm2                     Use iTerm2 instead of iTerm
    -i, --itermname NAME             Name of the application to use (default: iTerm)
    -f, --file FILE                  Cluster file (one hostname per line)
    -c, --cluster CLUSTERNAME        Name of the cluster specified in ~/.i2csshrc
    -r, --rank                       Send LC_RANK with the host number as environment variable
    -m, --machines a,b,c             Comma-separated list of hosts
    -s, --sleep SLEEP                Number of seconds to sleep between creating SSH sessions
    -X, --extra EXTRA_PARAM          Additional ssh parameters (e.g. -Xi=myidentity.pem)

i2cssh will assume you want to connect to a cluster when only one host is given.

For `-c` and `-m` options, the format `username@cluster` or `username@host` can be used.

The following commands are exactly the same, however, they might serve different purposes:

    $ i2cssh -m user1@host1,user2@host2
    $ i2cssh user1@host1 user2@host2

Using the `-l` option will override all usernames:

    $ i2cssh -l foo user1@host1 user2@host2

This will connect to both `host1` and `host2` as the user `foo`

## i2csshrc

The `i2csshrc` file is a YAML formatted file that contains the following structure:

    ---
    version: 2
    [optional parameters]
    clusters:
      mycluster:
        [optional parameters]
        hosts:
          - host1
          - host2

Optional parameters can be used globablly or per cluster and include:

    broadcast: (true/false)     # Enable/disable broadcast on start
    login: <username>           # Use this username for login
    profile: <iTerm2 profile>   # Use this iTerm profile
    rank: (true/false)          # Enable sending LC_RANK as an environment variable
    columns: <cols>             # Amount of columns
    rows: <rows>                # Amount of rows
    sleep: <secs>               # Seconds to sleep between creating SSH sessions
    direction: (column/row)     # Direction that new sessions are created (default: column)
    itermname:                  # iTerm app name (default: iTerm)

    environment:                # Send the following enviroment variables
        - LC_FOO: foo
        - LC_BAR: bar
    
    iterm2: true                # Use iTerm2.app instead of iTerm.app (only available globally)

Note: rows and columns can't be used together.

The following precedence is used:

`global options from config` < `cluster options from config` < `command line flags`

Make sure the config file is valid YAML (e.g. use spaces instead of tabs)

## Options

### -A, --forward-agent

Enable SSH agent forwarding

### -l, --login LOGIN

This option will override all logins passed in to i2cssh. This goes for global config, cluster config or username@host passed on the command line

### -e, --environment KEY=VAL

Allows for passing environment varables to the SSH session. This can be a comma-separated list: `-e LC_FOO=foo,LC_BAR=bar`

### -F, --fullscreen

Enable fullscreen on startup

### -C, --columns COLUMNS

Set the amount of columns. Can't be used in conjunction with -R

### -R, --rows ROWS

Set the amount of columns. Can't be used in conjunction with -C

### -b, --broadcast

Enable broadcast on startup. i2cssh will send cmd-shift-i to the window and press the OK button.

### -nb, --nobroadcast

Disable broadcast. This setting can be used to disable any broadcast that was set in the config.

### -p, --profile PROFILE

Use a specific iTerm profile

### -2, --iterm2

Use iTerm2.app instead of iTerm.app

### -i, --itermname NAME

Name of the application to use (default: iTerm). It happens sometimes iTerm isn't called iTerm. Use this parameter to override what app i2cssh interacts with.

### -f, --file

Will read nodes from a file. These will be added to any hosts specified on the command line or in the config

### -c, --cluster

Connect to a cluster that is specified in the config

### -r, --rank

Send a LC_RANK environment variable different for each host (from 0 to n)

### -m, --machines a,b,c

Connect to the machines a, b and c

### -s, --sleep SLEEP

Wait SLEEP seconds between starting each ssh session. This will take decimals as well (0.5 for half a second)

### -X, --extra EXTRA

Set extra ssh parameters in the form -Xk=v. For example:

    i2cssh -Xi=myidentity.pem

will result in 

    ssh -i myidentity.pem

Or,

    i2cssh -Xp=2222 -XL=8080:localhost:8080

will result in

    ssh -p 2222 -L 8080:localhost:8080

## Known issues

- i2cssh uses rb-appscript and that only seems to work on ruby 1.8.7 and breaks on 1.9.x
- appscript is no longer supported (http://appscript.sourceforge.net/status.html). This means that i2cssh might have to move to something else in the future. I haven't really looked at anything, but let me know if you find a good alternative!

## TODO

- Functional parity with csshX (as far as possible)
- -X support in config file

## Contributing to i2cssh

I know that i2cssh doesn't have all the functionality of csshX, but either let me know what you really need or 
fork, hack and create a pull request.
 
 * Check out the latest master to make sure the feature hasn't been implemented or the bug hasn't been fixed yet
 * Check out the issue tracker to make sure someone already hasn't requested it and/or contributed it
 * Fork the project
 * Start a feature/bugfix branch
 * Commit and push until you are happy with your contribution
 * Make sure to add tests for it. This is important so I don't break it in a future version unintentionally.
 * Please try not to mess with the Rakefile, version, or history. If you want to have your own version, or is otherwise necessary, that is fine, but please isolate to its own commit so I can cherry-pick around it.

## Copyright

Copyright (c) 2011-2012 Wouter de Bie. See LICENSE.txt for
further details.

