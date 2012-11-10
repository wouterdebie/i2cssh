require 'appscript'

class I2Cssh
    def initialize servers, ssh_options, i2_options, ssh_environment
        @ssh_prefix         = "ssh " + ssh_options.join(' ')
        @ssh_options        = ssh_options
        @i2_options         = i2_options
        @servers            = servers
        @ssh_environment    = ssh_environment

        app_name = (i2_options[:iterm2]) ? 'iTerm2' : 'iTerm'

        raise Exception.new 'No servers given' if servers.empty?

        @sys_events = Appscript.app.by_name('System Events')
        @iterm = Appscript.app.by_name(app_name)
        @term = @iterm.make(:new => :terminal)

        @profile = i2_options[:profile] || "Default"

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
        first = true
        if @i2_options[:open_by_row] then
            2.upto @rows do
              @sys_events.keystroke "D", :using => :command_down
            end
            2.upto @columns do
              1.upto @rows do
                @sys_events.key_code 126, :using => [:command_down, :option_down] unless first
                first = false
              end
              @rows.times do |x|
                @sys_events.keystroke "d", :using => :command_down
                @sys_events.key_code 125, :using => [:command_down, :option_down] unless @columns - 1 == x
              end
            end
        else
            2.upto @columns do
              @sys_events.keystroke "d", :using => :command_down
            end
            2.upto @rows do
              1.upto @columns do
                @sys_events.key_code 123, :using => [:command_down, :option_down] unless first
                first = false
              end
              @columns.times do |x|
                @sys_events.keystroke "D", :using => :command_down
                @sys_events.key_code 124, :using => [:command_down, :option_down] unless @columns - 1 == x
              end
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
                ssh_env = ""

                if @i2_options[:rank] then
                    @ssh_environment['LC_RANK'] = i-1
                end

                if !@ssh_environment.empty? then
                    send_env = "-o SendEnv=#{@ssh_environment.keys.join(",")}"
                    @term.sessions[i].write :text => "#{@ssh_environment.map{|k,v| "export #{k}=#{v}"}.join('; ')}"
                end

                @term.sessions[i].write :text => "unset HISTFILE && echo -e \"\\033]50;SetProfile=#{@profile}\\a\" && #{@ssh_prefix} #{send_env} #{server}"
            else
                
                @term.sessions[i].write :text => "unset HISTFILE && echo -e \"\\033]50;SetProfile=#{@profile}\\a\""
                sleep 0.3
                @term.sessions[i].foreground_color.set "red"
                @term.sessions[i].write :text => "stty -isig -icanon -echo && echo -e '#{"\n"*100}UNUSED' && cat > /dev/null"
            end
        end
    end
end
