# i2cssh

i2cssh is a http://code.google.com/p/csshx/ like tool for connecting over ssh to multiple machines. But instead of creating separate windows and having
a master window for input, i2cssh uses iterm2 split panes and "Send input to all sessions" (cmd-shift-i) to send commands
to all sessions.

## Installing 

    $ gem install i2cssh

## Usage
    Usage: i2cssh [options] [login@machine] [login@cluster]
    -A, --forward-agent              Enable SSH agent forwarding
    -l, --login LOGIN                SSH login name
    -F, --fullscreen                 Make the window fullscreen
    -C, --columns COLUMNS            Number of columns (rows will be calculated)
    -R, --rows ROWS                  Number of rows (columns will be calculated)
    -b, --broadcast                  Start with broadcast input (DANGEROUS!)
    -nb, --nobroadcast               Disable broadcast
    -p, --profile PROFILE            Name of the iTerm2 profile (default: Default)
    -2, --iterm2                     Use iTerm2 instead of iTerm
    -f, --file FILE                  Cluster file (one hostname per line)
    -c, --cluster CLUSTERNAME        Name of the cluster specified in ~/.i2csshrc
    -m, --machines a,b,c             Comma-separated list of hosts

For -c and -m options, the format username@cluster or username@host.

## i2csshrc

The i2csshrc file is a YAML formatted file that contains the following structure:

    ---
    version: 2             # Mandatory. Current version is 2
    iterm2: false           # Optional. Set to true if you use iTerm2.app instead of iTerm.app.
    broadcast: false        # Optional. Set to true if you want to enable broadcast for all clusters.
    login: myusername       # Optional. Always use this username.
    clusters:
      mycluster:
        broadcast: false    # Optional. Set to true if you want to enable broadcast for this cluster.
        login: false        # Optional. Set to true if you want a specific login for this cluster.
        hosts:
          - host1
          - host2
          - ...

The following precedence is used:

global options from config < cluster options from config < command line flags

Make sure the config file is valid YAML (e.g. use spaces instead of tabs)

## Known issues

- i2cssh uses rb-appscript and that only seems to work on ruby 1.8.7 and breaks on 1.9.x
- Only a single username can be used when using -m username@host.

## TODO

- Functional parity with csshX (as far as possible)

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

