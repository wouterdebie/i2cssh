require 'appscript'
class I2Cssh
    def initialize servers, ssh_options, i2_options, ssh_environment
        @ssh_prefix         = "ssh " + ssh_options.join(' ')
        @ssh_options        = ssh_options
        @i2_options         = i2_options.clone
        @servers            = servers
        @ssh_environment    = ssh_environment

        raise Exception.new 'No servers given' if servers.empty?

        @sys_events = Appscript.app.by_name('System Events')
        @iterm = Appscript.app.by_name("iTerm")

        @pane_menu = @sys_events.processes["iTerm2"].menu_bars[1].menu_bar_items["Window"].menus["Window"].menu_items["Select Split Pane"].menus["Select Split Pane"]
        @shell_menu = @sys_events.processes["iTerm2"].menu_bars[1].menu_bar_items["Shell"].menus["Shell"]

        @profile = i2_options.first[:profile] || "Default"

        @iterm.create_window_with_profile(@profile, :command => "/usr/bin/env bash -l")
        @window = @iterm.current_window

        while !@servers.empty? do
            compute_geometry
            split_session
            start_ssh
            enable_broadcast if i2_options.first[:broadcast]
            @servers.shift
            @i2_options.shift
            @ssh_environment.shift

            if !@servers.empty?  && i2_options.first[:tabs] then
                # @iterm.create_tab(@profile)
                @window.create_tab_with_default_profile()
                @session_index = 0
            end
        end
        @window.select(@window.tabs[1])
    end

    private
    def maximize(app_name)
        begin
            # OSX >= 10.8 has different behavior for full screen. First try out old behavior.
            fullscreen_bounds = Appscript.app.by_name('Finder').desktop.window.bounds
            window = @iterm.windows.get.sort_by{|x| x.id_.get}.last
            window.bounds.set fullscreen_bounds.get
        rescue
            @sys_events.processes[app_name].windows.first.attributes["AXFullScreen"].value.set(true)
        end
    end

    def compute_geometry
        # Create geometry when combining and ignore rows/columns preference
        if @servers.size > 1 && !@i2_options.first[:tabs]
            count = 0
            @servers.each do |srv|
                count += srv.size
            end
        else
            count = @servers.first.size
            @rows = @i2_options.first[:rows]
            @columns = @i2_options.first[:columns]
        end

        if @rows then
            @columns = (count / @rows.to_f).ceil
        elsif @columns then
            @rows = (count / @columns.to_f).ceil
        else
            @columns = Math.sqrt(count).ceil
            @rows = (count / @columns.to_f).ceil
        end
        # Quick hack: iTerms default window only supports up to 11 rows and 22 columns
        # If we surpass either one, we resort to full screen.
        if @rows > 11 or @columns > 22 then
            @i2_options.first[:fullscreen] = true
        end
    end

    def split_session
        left = @pane_menu.menu_items["Select Pane Left"]
        right = @pane_menu.menu_items["Select Pane Right"]
        up = @pane_menu.menu_items["Select Pane Above"]
        down = @pane_menu.menu_items["Select Pane Below"]

        split_vert = lambda { @window.current_session.split_vertically_with_same_profile }
        split_hori = lambda { @window.current_session.split_horizontally_with_same_profile }

        splitmap = {
            :column => {0 => split_vert, 1 => left, 2 => split_hori, 3=> right, :x => @columns, :y => @rows},
            :row => {0 => split_hori, 1=> up, 2 => split_vert, 3=> down, :x => @rows, :y => @columns}
        }
        splitconfig = splitmap[@i2_options.first[:direction]]

        first = true
        2.upto splitconfig[:x] do
            splitconfig[0].call
        end
        2.upto splitconfig[:y] do
            1.upto splitconfig[:x] do
                splitconfig[1].click
                first = false
            end
            splitconfig[:x].times do |x|
                splitconfig[2].call
                splitconfig[3].click
            end
        end
    end

    def enable_broadcast
        @sys_events.keystroke "I", :using => :command_down
        sleep 0.5
        @sys_events.keystroke "\r"
    end

    def start_ssh
        old_size = 0

        1.upto(@rows*@columns) do |i|
            tab = @window.current_tab
            session = tab.sessions[i]
            session.write :text => "/usr/bin/env bash -l"

            # Without the tab flag, combine all servers and clusters into one window
            if !@servers.empty? && (i - old_size) > @servers.first.size && !@i2_options.first[:tabs]
                old_size = @servers.first.size
                @servers.shift
                @i2_options.shift
                @ssh_environment.shift
            end

            if @servers.empty?
                server = nil
            else
                server = @servers.first[i-old_size-1]
            end


            if server then
                send_env = ""

                if @i2_options.first[:rank] then
                    @ssh_environment.first['LC_RANK'] = i-1
                end

                if !@ssh_environment.empty? && !@ssh_environment.first.empty? then
                    send_env = "-o SendEnv=#{@ssh_environment.first.keys.join(",")}"
                    session.write :text => "#{@ssh_environment.first.map{|k,v| "export #{k}=#{v}"}.join('; ')}"
                end
                if @i2_options.first[:sleep] then
                    sleep @i2_options.first[:sleep] * i
                end
                session.write :text => "unset HISTFILE && echo -e \"\\033]50;SetProfile=#{@profile}\\a\" && #{@ssh_prefix} #{send_env} #{server}"
            else

                session.write :text => "unset HISTFILE && echo -e \"\\033]50;SetProfile=#{@profile}\\a\""
                sleep 0.3
                session.foreground_color.set ([65535,0,0])
                session.write :text => "stty -isig -icanon -echo && echo -e '#{"\n"*100}UNUSED' && cat > /dev/null"
            end
        end
    end
end
