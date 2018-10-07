###
# autocomplete for i2cssh
# To allow autocomplete, add  the following 
#   to your .bash_profile, .bashrc or .profile
#  source [path to i2cssh-autocomplete.bash]
#

_complete_i2cssh_hosts () {
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    cmd="f=File.expand_path('~/.i2csshrc'); hash = YAML.load(File.read(f)); puts hash['clusters'].keys;";
    host_list=$(ruby  -r yaml <<< $cmd);
    COMPREPLY=( $(compgen -W "${host_list}" -- $cur))
    return 0
}

complete -F _complete_i2cssh_hosts i2cssh