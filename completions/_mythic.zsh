#compdef mythic
# zsh completion for mythic
# Install: copy to a directory in $fpath, e.g. ~/.zsh/completions/_mythic

_mythic() {
    local -a commands
    commands=(
        'run:Run one task for humans or AI callers'
        'chat:Start the terminal conversation loop'
        'tui:Start the optional Textual interface'
        'sessions:List or export workspace sessions as JSON'
    )

    local curcontext="$curcontext" state line
    typeset -A opt_args

    _arguments -C \
        '(-h --help)'{-h,--help}'[show help]' \
        '--version[show version]' \
        '1: :->command' \
        '*:: :->args' && return 0

    case $state in
        command)
            _describe 'command' commands
            ;;
        args)
            case $line[1] in
                run)
                    _arguments \
                        '--workspace[Project directory]:directory:_files -/' \
                        '--model[Model override]:model:' \
                        '--base-url[OpenAI-compatible endpoint]:url:' \
                        '--resume[Resume session by ID]:session:' \
                        '--permission[Permission mode]:mode:(read-only ask trusted)' \
                        '--format[Output format]:format:(plain json jsonl)' \
                        '*:prompt:'
                    ;;
                chat)
                    _arguments \
                        '--workspace[Project directory]:directory:_files -/'
                    ;;
                sessions)
                    _arguments \
                        '--workspace[Project directory]:directory:_files -/' \
                        '--export[Export transcript]:session:'
                    ;;
            esac
            ;;
    esac
}

_mythic "$@"
