require 'appscript'

class I2Cssh
    def initialize servers, ssh_options, i2_options
        @ssh_prefix  = "ssh " + ssh_options.join(' ')
        @ssh_options = ssh_options
        @i2_options  = i2_options
        @servers     = servers

        raise Exception.new 'No servers given' if servers.empty?

        @sys_events = Appscript.app.by_name('System Events')
        @iterm = Appscript.app.by_name('iTerm')
        @term = @iterm.make(:new => :terminal)
        session = @term.sessions.after.make :new => :session
        session.exec :command => "/bin/bash -l"

        compute_geometry
        split_session
        maximize if i2_options[:fullscreen]
        
        start_ssh
        enable_broadcast if i2_options[:broadcast]
    end

    private
    def maximize
      fullscreen_bounds = Appscript.app.by_name('Finder').desktop.window.bounds
      window = @iterm.windows.get.sort_by{|x| x.id_.get}.last
      window.bounds.set fullscreen_bounds.get
    end

    def compute_geometry
        count = @servers.size
        @rows = @i2_options[:rows]
        @columns = @i2_options[:columns]

        if @rows then
          @columns = (count / @rows.to_f).ceil
        elsif @columns then
          @rows = (count / @columns.to_f).ceil
        else
          @columns = Math.sqrt(count).ceil
          @rows = (count / @columns.to_f).ceil
        end
    end

    def split_session
        2.upto @columns do
          @sys_events.keystroke "d", :using => :command_down
        end
        2.upto @rows do
          1.upto @columns do
            @sys_events.key_code 123, :using => [:command_down, :option_down]
          end
          @columns.times do |x|
            @sys_events.keystroke "D", :using => :command_down
            @sys_events.key_code 124, :using => [:command_down, :option_down] unless @columns - 1 == x
          end
        end
    end

    def enable_broadcast
        @sys_events.keystroke "I", :using => :command_down
        sleep 0.5
        @sys_events.keystroke "\r"
    end

    def start_ssh
        1.upto(@rows*@columns) do |i|
            server = @servers[i-1]
            if server then
                @term.sessions[i].write :text => "unset HISTFILE && #{@ssh_prefix} #{server}"
            else
                @term.sessions[i].foreground_color.set "red"
                @term.sessions[i].write :text => "unset HISTFILE && stty -isig -icanon -echo && echo -e '#{"\n"*100}UNUSED' && cat > /dev/null"
            end
        end
    end
end
