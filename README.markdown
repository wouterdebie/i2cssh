# i2cssh

i2cssh is a http://code.google.com/p/csshx/ like tool for connecting over ssh to multiple machines. But instead of creating separate windows and having
a master window for input, i2cssh uses iterm2 split panes and "Send input to all sessions" (cmd-shift-i) to send commands
to all sessions.

## Installing 

    $ gem install i2cssh

## Usage

    Usage: i2cssh [options]
        -d, --debug                      Start RIPL after creating terminals
        -f, --file FILE                  Cluster file
        -F, --fullscreen                 Fullscreen
        -g, --grid WxH                   Grid size
        -u, --username USERNAME          SSH username
        -c, --cluster CLUSTERNAME        Name of the cluster specified in ~/.i2csshrc

The cluster file format is one host per line.

## i2csshrc

The i2csshrc file is a YAML formatted file that contains the following structure:

    ---
    clusters:
      mycluster:
        - host1
        - host2
        - ...

## Contributing to i2cssh
 
 * Check out the latest master to make sure the feature hasn't been implemented or the bug hasn't been fixed yet
 * Check out the issue tracker to make sure someone already hasn't requested it and/or contributed it
 * Fork the project
 * Start a feature/bugfix branch
 * Commit and push until you are happy with your contribution
 * Make sure to add tests for it. This is important so I don't break it in a future version unintentionally.
 * Please try not to mess with the Rakefile, version, or history. If you want to have your own version, or is otherwise necessary, that is fine, but please isolate to its own commit so I can cherry-pick around it.

## Copyright

Copyright (c) 2011 Wouter de Bie. See LICENSE.txt for
further details.

