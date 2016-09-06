require 'helper'

class TestExpandServers < Test::Unit::TestCase
    def expand input, expected
        assert_equal(expected, ExpandServers.expand_servers(input).join(' '))
    end


    should "no-op when no servers sent in" do
        expand ['test123.com'], 'test123.com'
    end

    should "expand simple number ranges" do
        expand ['test[1..3]'], 'test1 test2 test3'
    end

    should "expand simple lists" do
        expand ['test[sql,app,test]'], 'testsql testapp testtest'
    end

    should "expand recursively" do
        expand ['[sql,app][1..3]'], 'sql1 sql2 sql3 app1 app2 app3'
    end
end
