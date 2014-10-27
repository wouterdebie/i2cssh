require 'appscript'

class I2Cssh
    def initialize servers, ssh_options, i2_options, ssh_environment
        @ssh_prefix         = "ssh " + ssh_options.join(' ')
        @ssh_options        = ssh_options
        @i2_options         = i2_options
        @servers            = servers
        @ssh_environment    = ssh_environment

        app_name = (i2_options[:iterm2]) ? 'iTerm2' : ((i2_options[:itermname]) ? i2_options[:itermname] : 'iTerm')

        raise Exception.new 'No servers given' if servers.empty?

        @sys_events = Appscript.app.by_name('System Events')
        @iterm = Appscript.app.by_name(app_name)

        @pane_menu = @sys_events.processes[app_name].menu_bars[1].menu_bar_items["Window"].menus["Window"].menu_items["Select Split Pane"].menus["Select Split Pane"]
        @shell_menu = @sys_events.processes[app_name].menu_bars[1].menu_bar_items["Shell"].menus["Shell"]
        @term = @iterm.make(:new => :terminal)

        @profile = i2_options[:profile] || "Default"

        session = @term.sessions.after.make :new => :session
        session.exec :command => "/bin/bash -l"

        compute_geometry
        maximize(app_name) if i2_options[:fullscreen]
        split_session
        start_ssh
        enable_broadcast if i2_options[:broadcast]
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
        # Quick hack: iTerms default window only supports up to 11 rows and 22 columns
        # If we surpass either one, we resort to full screen.
        if @rows > 11 or @columns > 22 then
            @i2_options[:fullscreen] = true
        end
    end

    def split_session
        left = @pane_menu.menu_items["Select Pane Left"]
        right = @pane_menu.menu_items["Select Pane Right"]
        up = @pane_menu.menu_items["Select Pane Above"]
        down = @pane_menu.menu_items["Select Pane Below"]


        begin
            split_vert = @shell_menu.menu_items["Split Vertically"]
            split_hori = @shell_menu.menu_items["Split Horizontally"]
            split_vert.get
            split_hori.get
        rescue
            split_vert = @shell_menu.menu_items["Split Vertically with Current Profile"]
            split_hori = @shell_menu.menu_items["Split Horizontally with Current Profile"]
        end

        splitmap = {
            :column => {0 => split_vert, 1 => left, 2 => split_hori, 3=> right, :x => @columns, :y => @rows},
            :row => {0 => split_hori, 1=> up, 2 => split_vert, 3=> down, :x => @rows, :y => @columns}
        }
        splitconfig = splitmap[@i2_options[:direction]]

        first = true
        2.upto splitconfig[:x] do
            splitconfig[0].click
        end
        2.upto splitconfig[:y] do
            1.upto splitconfig[:x] do
                splitconfig[1].click
                first = false
            end
            splitconfig[:x].times do |x|
                splitconfig[2].click
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
        1.upto(@rows*@columns) do |i|
            @term.sessions[i].write :text => "/bin/bash -l"

            server = @servers[i-1]
            if server then
                send_env = ""

                if @i2_options[:rank] then
                    @ssh_environment['LC_RANK'] = i-1
                end

                if !@ssh_environment.empty? then
                    send_env = "-o SendEnv=#{@ssh_environment.keys.join(",")}"
                    @term.sessions[i].write :text => "#{@ssh_environment.map{|k,v| "export #{k}=#{v}"}.join('; ')}"
                end
                if @i2_options[:sleep] then
                    sleep @i2_options[:sleep] * i
                end
                if (server.class == Hash) then
                    server_name = server["name"]
                    if (server.has_key? "login") then
                        server_name = "#{server['login']}@#{server_name.gsub(/.+@/,'')}"
                    end
                    @term.sessions[i].write :text => "unset HISTFILE && echo -e \"\\033]50;SetProfile=#{@profile}\\a\" && #{@ssh_prefix} #{send_env} #{server_name}"
                    if (server.has_key? "command") then
                        @term.sessions[i].write :text => server["command"]
                    end
                 else
                    @term.sessions[i].write :text => "unset HISTFILE && echo -e \"\\033]50;SetProfile=#{@profile}\\a\" && #{@ssh_prefix} #{send_env} #{server}"
                 end
            else
                @term.sessions[i].write :text => "unset HISTFILE && echo -e \"\\033]50;SetProfile=#{@profile}\\a\""
                sleep 0.3
                @term.sessions[i].foreground_color.set "red"
                @term.sessions[i].write :text => "stty -isig -icanon -echo && echo -e '#{"\n"*100}UNUSED' && cat > /dev/null"
            end
        end
    end
end
