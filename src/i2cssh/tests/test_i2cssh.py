import asyncio
import copy
import unittest
from email.policy import default
from unittest.mock import ANY, AsyncMock, MagicMock, call, mock_open, patch

import pytest
from click.testing import CliRunner

import i2cssh
from i2cssh.lib import app
from i2cssh.version import version


def test_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert result.output.startswith("Usage:")


def test_version():
    runner = CliRunner()
    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert result.output.startswith(version())


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_sleep(sleep_moc: AsyncMock):
    await i2cssh.lib.sleep(1)
    sleep_moc.assert_called_once_with(1)


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_create_unused_pane(sleep_moc: AsyncMock):
    pane = AsyncMock()
    profile = AsyncMock()
    pane.async_get_profile.return_value = profile
    await i2cssh.lib.create_unused_pane(pane)
    pane.async_get_profile.assert_called_once()
    sleep_moc.assert_called_once_with(0.3)
    profile.async_set_foreground_color.assert_called_once()
    pane.async_send_text.assert_has_calls(
        [
            call("unset HISTFILE\n"),
            call(
                "stty -isig -icanon -echo && echo -e '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nUNUSED' && cat > /dev/null\n"
            ),
        ]
    )


@pytest.mark.asyncio
async def test_fullscreen():
    window = AsyncMock()
    await i2cssh.lib.set_fullscreen(window)
    window.async_set_fullscreen.assert_called_once_with(True)


@pytest.mark.asyncio
@patch("iterm2.async_get_app", new_callable=AsyncMock)
async def test_get_window(iterm_mock: AsyncMock):
    connection = AsyncMock()
    await i2cssh.lib.get_window(connection)
    iterm_mock.assert_called_once_with(connection)


@pytest.mark.asyncio
async def test_execute_command():
    pane = AsyncMock()
    cmd = MagicMock()
    await i2cssh.lib.execute_command(pane, cmd)
    pane.async_send_text.assert_called_once_with(cmd)


def test_get_host_strs_from_file():
    with patch("builtins.open", mock_open(read_data="foo\nbar\n")):
        assert i2cssh.lib.get_host_strs_from_file("foo") == ["foo", "bar"]


def invoke(args, config):
    with patch("i2cssh.lib.read_config") as mock_read_config, patch(
        "i2cssh.lib.get_window"
    ), patch("iterm2.run_until_complete", run_until_complete_mock):
        mock_read_config.return_value = config
        runner = CliRunner()
        result = runner.invoke(app, args)
        assert result.exit_code == 0
        return result


def run_until_complete_mock(target):
    connection = MagicMock()()
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(target(connection))]
    loop.run_until_complete(asyncio.wait(tasks))


class TestReadConfig(unittest.TestCase):
    @patch("os.path.isfile", return_value=True)
    @patch("builtins.open", mock_open(read_data="@"))
    @patch("sys.exit")
    def test_read_test_read_config_invalid_yaml(
        self, exit_mock: MagicMock, open_mock: MagicMock
    ):
        i2cssh.lib.read_config()
        exit_mock.assert_called_once_with(252)

    @patch("os.path.isfile", return_value=True)
    @patch("builtins.open", mock_open(read_data="version: 2\nfoo: bar\n"))
    def test_read_config(self, open_mock: MagicMock):
        assert i2cssh.lib.read_config() == {"foo": "bar", "version": 2}


default_config = {
    "clusters": {
        "foo": {
            "hosts": ["foo1", "foo2"],
        }
    }
}


def assert_options(mec, options, hosts=["foo1", "foo2"], extra_calls=[]):
    if options:
        options = f"{options} "

    calls = [call(ANY, f"unset HISTFILE && ssh {options}{host}\n") for host in hosts]
    if len(extra_calls) > 0:
        calls += [call(ANY, extra_call) for extra_call in extra_calls]

    mec.assert_has_calls(
        calls,
        any_order=True,
    )


@patch("i2cssh.lib.execute_command")
class TestParams(unittest.TestCase):
    def test_no_args(self, mec: MagicMock):
        with patch("i2cssh.lib.read_config") as mock_read_config, patch(
            "i2cssh.lib.get_window"
        ), patch("iterm2.run_until_complete", run_until_complete_mock):
            mock_read_config.return_value = default_config
            runner = CliRunner()
            result = runner.invoke(app)
            assert result.exit_code == 255

    def test_unknown_cluster(self, mec: MagicMock):
        with patch("i2cssh.lib.read_config") as mock_read_config, patch(
            "i2cssh.lib.get_window"
        ), patch("iterm2.run_until_complete", run_until_complete_mock):
            mock_read_config.return_value = default_config
            runner = CliRunner()
            result = runner.invoke(app, ["unknown_cluster"])
            assert result.exit_code == 254

    def test_unknown_clusters_cli(self, mec: MagicMock):
        with patch("i2cssh.lib.read_config") as mock_read_config, patch(
            "i2cssh.lib.get_window"
        ), patch("iterm2.run_until_complete", run_until_complete_mock):
            mock_read_config.return_value = default_config
            runner = CliRunner()
            result = runner.invoke(app, ["-c", "unknown_cluster"])
            assert result.exit_code == 254

    def test_no_current_window_cli(self, mec: MagicMock):
        with patch("i2cssh.lib.read_config") as mock_read_config, patch(
            "i2cssh.lib.get_window"
        ) as mock_get_window, patch(
            "iterm2.run_until_complete", run_until_complete_mock
        ):
            mock_read_config.return_value = default_config
            mock_get_window.return_value = None
            runner = CliRunner()
            result = runner.invoke(app, ["-c", "foo"])
            assert result.exit_code == 253

    def test_clusters_cli(self, mec: MagicMock):
        invoke(["-c", "foo"], default_config)
        assert_options(mec, "")

    @patch("i2cssh.lib.create_tab")
    @patch("i2cssh.lib.create_window")
    def test_multiple_clusters_cli(
        self, mock_create_window: MagicMock, mock_create_tab: MagicMock, mec: MagicMock
    ):
        config = {
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "hosts": ["bar1", "bar2"],
                },
            }
        }
        invoke(["-c", "foo,bar"], config)
        assert_options(mec, "", ["foo1", "foo2", "bar1", "bar2"])
        mock_create_window.assert_called_once()
        self.assertEqual(mock_create_tab.call_count, 0)

    def test_include_from(self, mec: MagicMock):
        config = {
            "clusters": {
                "foo": {
                    "include_from": ["bar"],
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "hosts": ["bar1", "bar2"],
                },
            }
        }
        invoke(["foo"], config)
        assert_options(mec, "", ["foo1", "foo2", "bar1", "bar2"])

    @patch("i2cssh.lib.create_tab")
    @patch("i2cssh.lib.create_window")
    def test_tab_split_clusters_cli(
        self, mock_create_window: MagicMock, mock_create_tab: MagicMock, mec: MagicMock
    ):
        config = {
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "hosts": ["bar1", "bar2"],
                },
                "baz": {
                    "hosts": ["baz1", "baz2"],
                },
            }
        }
        invoke(["-c", "foo,bar,baz", "-t"], config)
        assert_options(mec, "", ["foo1", "foo2", "bar1", "bar2", "baz1", "baz2"])
        mock_create_window.assert_called_once()
        self.assertEqual(mock_create_tab.call_count, 2)

    @patch("i2cssh.lib.create_tab")
    @patch("i2cssh.lib.create_window")
    def test_tab_split_clusters_global_config(
        self, mock_create_window: MagicMock, mock_create_tab: MagicMock, mec: MagicMock
    ):
        config = {
            "tab_split": True,
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "hosts": ["bar1", "bar2"],
                },
                "baz": {
                    "hosts": ["baz1", "baz2"],
                },
            },
        }
        invoke(["-c", "foo,bar,baz"], config)
        assert_options(mec, "", ["foo1", "foo2", "bar1", "bar2", "baz1", "baz2"])
        mock_create_window.assert_called_once()
        self.assertEqual(mock_create_tab.call_count, 2)

    @patch("i2cssh.lib.create_tab")
    @patch("i2cssh.lib.create_window")
    def test_tab_split_clusters_with_machines_cli(
        self, mock_create_window: MagicMock, mock_create_tab: MagicMock, mec: MagicMock
    ):
        config = {
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "hosts": ["bar1", "bar2"],
                },
            }
        }
        invoke(["-c", "foo,bar", "-m", "baz1,baz2", "-t"], config)
        assert_options(mec, "", ["foo1", "foo2", "bar1", "bar2", "baz1", "baz2"])
        mock_create_window.assert_called_once()
        self.assertEqual(mock_create_tab.call_count, 2)

    @patch("i2cssh.lib.create_tab")
    @patch("i2cssh.lib.create_window")
    def test_tab_split_no_group_clusters_with_machines_cli(
        self, mock_create_window: MagicMock, mock_create_tab: MagicMock, mec: MagicMock
    ):
        config = {
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "hosts": ["bar1", "bar2"],
                },
            }
        }
        invoke(["-c", "foo,bar", "-m", "baz1,baz2", "-T"], config)
        assert_options(mec, "", ["foo1", "foo2", "bar1", "bar2", "baz1", "baz2"])
        mock_create_window.assert_called_once()
        self.assertEqual(mock_create_tab.call_count, 3)

    @patch("i2cssh.lib.create_tab")
    @patch("i2cssh.lib.create_window")
    def test_tab_split_no_group_clusters_with_machines_global_config(
        self, mock_create_window: MagicMock, mock_create_tab: MagicMock, mec: MagicMock
    ):
        config = {
            "tab_split_nogroup": True,
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "hosts": ["bar1", "bar2"],
                },
            },
        }
        invoke(["-c", "foo,bar", "-m", "baz1,baz2"], config)
        assert_options(mec, "", ["foo1", "foo2", "bar1", "bar2", "baz1", "baz2"])
        mock_create_window.assert_called_once()
        self.assertEqual(mock_create_tab.call_count, 3)

    @patch("i2cssh.lib.create_tab")
    @patch("i2cssh.lib.create_window")
    def test_clusters_same_window_group_cli(
        self, mock_create_window: MagicMock, mock_create_tab: MagicMock, mec: MagicMock
    ):
        config = {
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "hosts": ["bar1", "bar2"],
                },
            }
        }
        invoke(["-c", "foo,bar", "-m", "baz1,baz2", "-W", "-t"], config)
        assert_options(mec, "", ["foo1", "foo2", "bar1", "bar2", "baz1", "baz2"])
        self.assertEqual(mock_create_window.call_count, 0)
        self.assertEqual(mock_create_tab.call_count, 3)

    @patch("i2cssh.lib.create_tab")
    @patch("i2cssh.lib.create_window")
    def test_clusters_same_window_no_group_cli(
        self, mock_create_window: MagicMock, mock_create_tab: MagicMock, mec: MagicMock
    ):
        config = {
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "hosts": ["bar1", "bar2"],
                },
            }
        }
        invoke(["-c", "foo,bar", "-m", "baz1,baz2", "-W"], config)
        assert_options(mec, "", ["foo1", "foo2", "bar1", "bar2", "baz1", "baz2"])
        self.assertEqual(mock_create_window.call_count, 0)
        self.assertEqual(mock_create_tab.call_count, 1)

    @patch("i2cssh.lib.create_tab")
    @patch("i2cssh.lib.create_window")
    def test_clusters_same_window_no_group_global_config(
        self, mock_create_window: MagicMock, mock_create_tab: MagicMock, mec: MagicMock
    ):
        config = {
            "same_window": True,
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "hosts": ["bar1", "bar2"],
                },
            },
        }
        invoke(["-c", "foo,bar", "-m", "baz1,baz2"], config)
        assert_options(mec, "", ["foo1", "foo2", "bar1", "bar2", "baz1", "baz2"])
        self.assertEqual(mock_create_window.call_count, 0)
        self.assertEqual(mock_create_tab.call_count, 1)

    def test_clusters_no_opts(self, mec: MagicMock):
        invoke(["foo"], default_config)
        assert_options(mec, "")

    def test_machines_cli(self, mec: MagicMock):
        invoke(["-m", "bar1,bar2"], default_config)
        assert_options(mec, "", ["bar1", "bar2"])

    def test_multiple_hosts_cli(self, mec: MagicMock):
        invoke(["bar1", "bar2"], default_config)
        assert_options(mec, "", ["bar1", "bar2"])

    @patch("i2cssh.lib.create_tab")
    @patch("i2cssh.lib.create_window")
    def test_hosts_same_window_no_group_cli(
        self, mock_create_window: MagicMock, mock_create_tab: MagicMock, mec: MagicMock
    ):
        invoke(["-T", "bar1", "bar2"], default_config)
        assert_options(mec, "", ["bar1", "bar2"])
        self.assertEqual(mock_create_window.call_count, 1)
        self.assertEqual(mock_create_tab.call_count, 1)

    @patch("i2cssh.lib.create_tab")
    @patch("i2cssh.lib.create_window")
    def test_hosts_same_window_no_group_cli(
        self, mock_create_window: MagicMock, mock_create_tab: MagicMock, mec: MagicMock
    ):
        invoke(["-t", "bar1", "bar2"], default_config)
        assert_options(mec, "", ["bar1", "bar2"])
        self.assertEqual(mock_create_window.call_count, 1)
        self.assertEqual(mock_create_tab.call_count, 0)

    def test_forward_agent_cli(self, mec: MagicMock):
        invoke(["foo", "-A"], default_config)
        assert_options(mec, "-A")

    def test_forward_agent_cluster_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["forward_agent"] = True
        invoke(["foo"], config)
        assert_options(mec, "-A")

    def test_forward_agent_global_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["forward_agent"] = True
        invoke(["foo"], config)
        assert_options(mec, "-A")

    def test_login_cli(self, mec: MagicMock):
        invoke(["foo", "-l", "myuser"], default_config)
        assert_options(mec, "", ["myuser@foo1", "myuser@foo2"])

    def test_login_cluster_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["login"] = "myuser"
        invoke(["foo"], config)
        assert_options(mec, "", ["myuser@foo1", "myuser@foo2"])

    def test_login_global_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["login"] = "myuser"
        invoke(["foo"], config)
        assert_options(mec, "", ["myuser@foo1", "myuser@foo2"])

    def test_login_host_config(self, mec: MagicMock):
        config = {
            "same_window": True,
            "clusters": {
                "foo": {
                    "hosts": ["myuser@foo1", "myuser@foo2"],
                },
            },
        }

        invoke(["foo"], config)
        assert_options(mec, "", ["myuser@foo1", "myuser@foo2"])

    def test_environment_cli(self, mec: MagicMock):
        invoke(["foo", "-e", "LC_FOO=foo,LC_BAR=bar"], default_config)
        assert_options(mec, "-o SendEnv=LC_FOO,LC_BAR")

    def test_environment_cluster_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["environment"] = {"LC_FOO": "foo", "LC_BAR": "bar"}
        invoke(["foo"], config)
        assert_options(
            mec,
            "-o SendEnv=LC_FOO,LC_BAR",
            extra_calls=["export LC_FOO=foo; export LC_BAR=bar;\n"],
        )

    def test_environment_global_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["environment"] = {"LC_FOO": "foo", "LC_BAR": "bar"}
        invoke(["foo"], config)
        assert_options(
            mec,
            "-o SendEnv=LC_FOO,LC_BAR",
            extra_calls=["export LC_FOO=foo; export LC_BAR=bar;\n"],
        )

    def test_rank_cli(self, mec: MagicMock):
        invoke(["foo", "-r"], default_config)
        assert_options(
            mec,
            "-o SendEnv=LC_RANK",
            extra_calls=["export LC_RANK=0;\n", "export LC_RANK=1;\n"],
        )

    def test_rank_cluster_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["rank"] = True
        invoke(["foo"], config)
        assert_options(
            mec,
            "-o SendEnv=LC_RANK",
            extra_calls=["export LC_RANK=0;\n", "export LC_RANK=1;\n"],
        )

    def test_rank_global_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["rank"] = True
        invoke(["foo"], config)
        assert_options(
            mec,
            "-o SendEnv=LC_RANK",
            extra_calls=["export LC_RANK=0;\n", "export LC_RANK=1;\n"],
        )

    def test_extra_cli(self, mec: MagicMock):
        invoke(["foo", "-Xi=myidentity.pem", "-Xp=2222", "-XZ"], default_config)
        assert_options(mec, "-i myidentity.pem -p 2222 -Z")

    def test_extra_cluster_config_list(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["extra"] = ["i=myidentity.pem", "p=2222", "Z"]
        invoke(["foo"], config)
        assert_options(mec, "-i myidentity.pem -p 2222 -Z")

    def test_extra_cluster_config_dict(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["extra"] = {"i": "myidentity.pem", "p": 2222}
        invoke(["foo"], config)
        assert_options(mec, "-i myidentity.pem -p 2222")

    def test_extra_global_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["extra"] = ["i=myidentity.pem", "p=2222"]
        invoke(["foo"], config)
        assert_options(mec, "-i myidentity.pem -p 2222")

    def test_gateway_cli(self, mec: MagicMock):
        invoke(["foo", "-g bar"], default_config)
        assert_options(mec, '-o ProxyCommand="ssh -W %h:%p bar"')

    def test_gateway_cluster_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["gateway"] = "bar"
        invoke(["foo"], config)
        assert_options(mec, '-o ProxyCommand="ssh -W %h:%p bar"')

    def test_gateway_global_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["gateway"] = "bar"
        invoke(["foo"], config)
        assert_options(mec, '-o ProxyCommand="ssh -W %h:%p bar"')

    def test_custom_command_cli(self, mec: MagicMock):
        invoke(["foo", "-x mycmd {host} -- bla"], default_config)

        mec.assert_has_calls(
            [
                call(ANY, f"unset HISTFILE && mycmd foo1 -- bla\n"),
                call(ANY, f"unset HISTFILE && mycmd foo2 -- bla\n"),
            ],
            any_order=True,
        )

    def test_custom_command_cluster_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["custom_command"] = "mycmd {host} -- bla"
        invoke(["foo"], config)

        mec.assert_has_calls(
            [
                call(ANY, f"unset HISTFILE && mycmd foo1 -- bla\n"),
                call(ANY, f"unset HISTFILE && mycmd foo2 -- bla\n"),
            ],
            any_order=True,
        )

    def test_custom_command_global_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["custom_command"] = "mycmd {host} -- bla"
        invoke(["foo"], config)

        mec.assert_has_calls(
            [
                call(ANY, f"unset HISTFILE && mycmd foo1 -- bla\n"),
                call(ANY, f"unset HISTFILE && mycmd foo2 -- bla\n"),
            ],
            any_order=True,
        )

    @patch("i2cssh.lib.set_fullscreen")
    def test_fullscreen_on_cli(self, mock_fullscreen: MagicMock, mec: MagicMock):
        invoke(["-c", "foo", "-F"], default_config)
        assert_options(mec, "")
        mock_fullscreen.assert_called_once()

    @patch("i2cssh.lib.set_fullscreen")
    def test_fullscreen_off_cli(self, mock_fullscreen: MagicMock, mec: MagicMock):
        invoke(["-c", "foo"], default_config)
        assert_options(mec, "")
        self.assertEqual(mock_fullscreen.call_count, 0)

    @patch("i2cssh.lib.set_fullscreen")
    def test_fullscreen_on_global_config(
        self, mock_fullscreen: MagicMock, mec: MagicMock
    ):
        config = copy.deepcopy(default_config)
        config["fullscreen"] = True
        invoke(["foo"], config)
        assert_options(mec, "")
        mock_fullscreen.assert_called_once()

    def test_precedence_cli(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["forward_agent"] = False
        config["forward_agent"] = False
        invoke(["foo", "-A"], config)
        assert_options(mec, "-A")

    def test_precedence_cluster_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["forward_agent"] = True
        config["forward_agent"] = False
        invoke(["foo"], config)
        assert_options(mec, "-A")

    def test_precedence_cluster_config_off(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["forward_agent"] = False
        config["forward_agent"] = True
        invoke(["foo"], config)
        assert_options(mec, "")

    def test_precedence_global_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["forward_agent"] = True
        invoke(["foo"], config)
        assert_options(mec, "-A")

    def test_use_exec_cli(self, mec: MagicMock):
        invoke(["foo", "-E"], default_config)

        mec.assert_has_calls(
            [
                call(ANY, f"unset HISTFILE && exec ssh -o ControlMaster=no foo1\n"),
                call(ANY, f"unset HISTFILE && exec ssh -o ControlMaster=no foo2\n"),
            ],
            any_order=True,
        )

    def test_use_exec_cluster_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["exec"] = True
        invoke(["foo"], config)

        mec.assert_has_calls(
            [
                call(ANY, f"unset HISTFILE && exec ssh -o ControlMaster=no foo1\n"),
                call(ANY, f"unset HISTFILE && exec ssh -o ControlMaster=no foo2\n"),
            ],
            any_order=True,
        )

    def test_use_exec_global_config(self, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["exec"] = True
        invoke(["foo"], config)

        mec.assert_has_calls(
            [
                call(ANY, f"unset HISTFILE && exec ssh -o ControlMaster=no foo1\n"),
                call(ANY, f"unset HISTFILE && exec ssh -o ControlMaster=no foo2\n"),
            ],
            any_order=True,
        )

    @patch("i2cssh.lib.set_broadcast_domains")
    def test_broadcast_on_cli(self, mock_broadcast: MagicMock, mec: MagicMock):
        invoke(["-c", "foo", "-b"], default_config)
        assert_options(mec, "")
        mock_broadcast.assert_has_calls([call(ANY, [ANY])])

    @patch("i2cssh.lib.set_broadcast_domains")
    def test_broadcast_off_cli(self, mock_broadcast: MagicMock, mec: MagicMock):
        invoke(["-c", "foo"], default_config)
        assert_options(mec, "")
        mock_broadcast.assert_has_calls([call(ANY, [])])

    @patch("i2cssh.lib.set_broadcast_domains")
    def test_broadcast_global_config(self, mock_broadcast: MagicMock, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["broadcast"] = True
        invoke(["foo"], config)
        assert_options(mec, "")
        mock_broadcast.assert_has_calls([call(ANY, [ANY])])

    @patch("i2cssh.lib.set_broadcast_domains")
    def test_broadcast_cluster_config(self, mock_broadcast: MagicMock, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["broadcast"] = True
        invoke(["foo"], config)
        assert_options(mec, "")
        mock_broadcast.assert_has_calls([call(ANY, [ANY])])

    @patch("i2cssh.lib.set_broadcast_domains")
    def test_broadcast_multiple_clusters(
        self, mock_broadcast: MagicMock, mec: MagicMock
    ):
        config = {
            "clusters": {
                "foo": {
                    "broadcast": False,
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "broadcast": True,
                    "hosts": ["bar1", "bar2"],
                },
            }
        }

        invoke(["-c", "foo,bar", "-t"], config)
        assert_options(mec, "")
        mock_broadcast.assert_has_calls([call(ANY, [ANY])])

    @patch("i2cssh.lib.set_broadcast_domains")
    def test_nobroadcast_on_cli(self, mock_broadcast: MagicMock, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["nobroadcast"] = True
        invoke(["-c", "foo", "-nb"], config)
        assert_options(mec, "")
        mock_broadcast.assert_has_calls([call(ANY, [])])

    @patch("i2cssh.lib.set_broadcast_domains")
    def test_broadcast_on_cluster_config_override(
        self, mock_broadcast: MagicMock, mec: MagicMock
    ):
        config = copy.deepcopy(default_config)
        config["broadcast"] = True
        config["clusters"]["foo"]["nobroadcast"] = True
        invoke(["foo"], config)
        assert_options(mec, "")
        mock_broadcast.assert_has_calls([call(ANY, [])])

    @patch("i2cssh.lib.set_broadcast_domains")
    def test_broadcast_multiple_clusters(
        self, mock_broadcast: MagicMock, mec: MagicMock
    ):
        config = {
            "broadcast": True,
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "nobroadcast": True,
                    "hosts": ["bar1", "bar2"],
                },
            },
        }

        invoke(["-c", "foo,bar", "-t"], config)
        assert_options(mec, "")
        mock_broadcast.assert_has_calls([call(ANY, [ANY])])

    @patch("i2cssh.lib.set_broadcast_domains")
    def test_broadcast_multiple_clusters_cli(
        self, mock_broadcast: MagicMock, mec: MagicMock
    ):
        config = {
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2"],
                },
                "bar": {
                    "nobroadcast": True,
                    "hosts": ["bar1", "bar2"],
                },
            },
        }

        invoke(["-c", "foo,bar", "-t", "-b"], config)
        assert_options(mec, "")
        mock_broadcast.assert_has_calls([call(ANY, [ANY])])

    @patch("i2cssh.lib.sleep")
    def test_sleep_cli(self, mock_sleep: MagicMock, mec: MagicMock):
        invoke(["-c", "foo", "-s", "1"], default_config)
        assert_options(mec, "")
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("i2cssh.lib.sleep")
    def test_sleep_cluster_config(self, mock_sleep: MagicMock, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["sleep"] = 1
        invoke(["-c", "foo", "-s", "1"], config)
        assert_options(mec, "")
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("i2cssh.lib.sleep")
    def test_sleep_global_config(self, mock_sleep: MagicMock, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["sleep"] = 1
        invoke(["-c", "foo", "-s", "1"], config)
        assert_options(mec, "")
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("i2cssh.lib.create_lwop")
    def test_shell_cli(self, mock_lwop: MagicMock, mec: MagicMock):
        invoke(["-c", "foo", "-S", "zsh"], default_config)
        assert_options(mec, "")
        mock_lwop.assert_has_calls([call("/usr/bin/env zsh -l")])

    @patch("i2cssh.lib.create_lwop")
    def test_shell_cluster_config(self, mock_lwop: MagicMock, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["clusters"]["foo"]["shell"] = "zsh"
        invoke(["-c", "foo"], config)
        assert_options(mec, "")
        mock_lwop.assert_has_calls([call("/usr/bin/env zsh -l")])

    @patch("i2cssh.lib.create_lwop")
    def test_shell_global_config(self, mock_lwop: MagicMock, mec: MagicMock):
        config = copy.deepcopy(default_config)
        config["shell"] = "zsh"
        invoke(["-c", "foo"], config)
        assert_options(mec, "")
        mock_lwop.assert_has_calls([call("/usr/bin/env zsh -l")])

    def test_compute_geometry(self, mec: MagicMock):
        self.assertEqual(
            i2cssh.lib.compute_geometry(20, 2, None),
            {"rows": 2, "cols": 10, "requires_fullscreen": False},
        )

        self.assertEqual(
            i2cssh.lib.compute_geometry(20, None, 2),
            {"rows": 10, "cols": 2, "requires_fullscreen": False},
        )

        self.assertEqual(
            i2cssh.lib.compute_geometry(21, 5, None),
            {"rows": 5, "cols": 5, "requires_fullscreen": False},
        )

        self.assertEqual(
            i2cssh.lib.compute_geometry(20, None, None),
            {"rows": 5, "cols": 4, "requires_fullscreen": False},
        )

        self.assertEqual(
            i2cssh.lib.compute_geometry(4, 10, None),
            {"rows": 10, "cols": 1, "requires_fullscreen": False},
        )

    @patch("i2cssh.lib.split_pane")
    def test_direction_default_cli(self, mock_split_pane: MagicMock, mec: MagicMock):
        config = {
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2", "foo3", "foo4"],
                }
            },
        }
        invoke(["-c", "foo"], config)
        assert_options(mec, "")
        self.assertEqual(mock_split_pane.call_count, 3)
        mock_split_pane.assert_has_calls(
            [
                call("Default", ANY, True, ANY),
                call("Default", ANY, False, ANY),
                call("Default", ANY, False, ANY),
            ]
        )

    @patch("i2cssh.lib.split_pane")
    def test_direction_row_cli(self, mock_split_pane: MagicMock, mec: MagicMock):
        config = {
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2", "foo3", "foo4"],
                }
            },
        }
        invoke(["-c", "foo", "-d", "row"], config)
        assert_options(mec, "")
        self.assertEqual(mock_split_pane.call_count, 3)
        mock_split_pane.assert_has_calls(
            [
                call("Default", ANY, False, ANY),
                call("Default", ANY, True, ANY),
                call("Default", ANY, True, ANY),
            ]
        )

    @patch("i2cssh.lib.split_pane")
    def test_direction_column_cli(self, mock_split_pane: MagicMock, mec: MagicMock):
        config = {
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2", "foo3", "foo4"],
                }
            },
        }
        invoke(["-c", "foo", "-d", "column"], config)
        assert_options(mec, "")
        self.assertEqual(mock_split_pane.call_count, 3)
        mock_split_pane.assert_has_calls(
            [
                call("Default", ANY, True, ANY),
                call("Default", ANY, False, ANY),
                call("Default", ANY, False, ANY),
            ]
        )

    @patch("i2cssh.lib.split_pane")
    def test_direction_row_global_config(
        self, mock_split_pane: MagicMock, mec: MagicMock
    ):
        config = {
            "direction": "row",
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2", "foo3", "foo4"],
                },
            },
        }
        invoke(["-c", "foo"], config)
        assert_options(mec, "")
        self.assertEqual(mock_split_pane.call_count, 3)
        mock_split_pane.assert_has_calls(
            [
                call("Default", ANY, False, ANY),
                call("Default", ANY, True, ANY),
                call("Default", ANY, True, ANY),
            ]
        )

    @patch("i2cssh.lib.split_pane")
    def test_direction_column_global_config(
        self, mock_split_pane: MagicMock, mec: MagicMock
    ):
        config = {
            "direction": "column",
            "clusters": {
                "foo": {
                    "hosts": ["foo1", "foo2", "foo3", "foo4"],
                },
            },
        }
        invoke(["-c", "foo"], config)
        assert_options(mec, "")
        self.assertEqual(mock_split_pane.call_count, 3)
        mock_split_pane.assert_has_calls(
            [
                call("Default", ANY, True, ANY),
                call("Default", ANY, False, ANY),
                call("Default", ANY, False, ANY),
            ]
        )

    @patch("i2cssh.lib.split_pane")
    def test_direction_row_cluster_config(
        self, mock_split_pane: MagicMock, mec: MagicMock
    ):
        config = {
            "clusters": {
                "foo": {
                    "direction": "row",
                    "hosts": ["foo1", "foo2", "foo3", "foo4"],
                },
            },
        }
        invoke(["-c", "foo"], config)
        assert_options(mec, "")
        self.assertEqual(mock_split_pane.call_count, 3)
        mock_split_pane.assert_has_calls(
            [
                call("Default", ANY, False, ANY),
                call("Default", ANY, True, ANY),
                call("Default", ANY, True, ANY),
            ]
        )

    @patch("i2cssh.lib.split_pane")
    def test_direction_column_cluster_config(
        self, mock_split_pane: MagicMock, mec: MagicMock
    ):
        config = {
            "clusters": {
                "foo": {
                    "direction": "column",
                    "hosts": ["foo1", "foo2", "foo3", "foo4"],
                },
            },
        }
        invoke(["-c", "foo"], config)
        assert_options(mec, "")
        self.assertEqual(mock_split_pane.call_count, 3)
        mock_split_pane.assert_has_calls(
            [
                call("Default", ANY, True, ANY),
                call("Default", ANY, False, ANY),
                call("Default", ANY, False, ANY),
            ]
        )

    @patch("i2cssh.lib.create_unused_pane")
    def test_direction_column_cluster_config(
        self, mock_create_unused_pane: MagicMock, mec: MagicMock
    ):
        config = {
            "clusters": {
                "foo": {
                    "direction": "column",
                    "hosts": ["foo1", "foo2", "foo3"],
                },
            },
        }
        invoke(["-c", "foo"], config)
        assert_options(mec, "")
        mock_create_unused_pane.assert_called_once()

    @patch("i2cssh.lib.get_host_strs_from_file")
    def test_file_cli(self, mock_get_host_strs_from_file: MagicMock, mec: MagicMock):
        mock_get_host_strs_from_file.return_value = ["bar1", "bar2"]
        invoke(["-f", "bar_hosts"], default_config)
        assert_options(mec, "", ["bar1", "bar2"])
