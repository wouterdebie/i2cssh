module ExpandServers
    def self.expand_servers servers
        memo = []
        servers.flatten.each do |server|
            needs_expanding = /(\[([^\]]+)\])/.match(server)
            if needs_expanding
                range = /([a-zA-Z0-9]+)\.\.([a-zA-Z0-9]+)/.match(needs_expanding.captures[1])
                if range
                    new_values = (range.captures[0]..range.captures[1])
                else # assume list
                    new_values = needs_expanding.captures[1].split(',')
                end

                new_servers = new_values.map do |new_val|
                    server.sub(needs_expanding.captures[0], new_val)
                end
                memo.concat(expand_servers(new_servers))
            else
                memo << server
            end
        end

        memo
    end
end
