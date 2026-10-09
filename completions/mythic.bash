# bash completion for mythic
# Install: copy to /etc/bash_completion.d/ or source from ~/.bashrc

_mythic_completions() {
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    commands="run chat tui sessions doctor"

    # Complete flag values
    case "$prev" in
        --permission)
            COMPREPLY=($(compgen -W "read-only ask trusted" -- "$cur"))
            return 0
            ;;
        --format)
            COMPREPLY=($(compgen -W "plain json jsonl" -- "$cur"))
            return 0
            ;;
        --workspace)
            COMPREPLY=($(compgen -d -- "$cur"))
            return 0
            ;;
    esac

    # Complete subcommand-specific flags
    local subcommand=""
    for word in "${COMP_WORDS[@]:1}"; do
        case "$word" in
            run|chat|tui|sessions) subcommand="$word"; break ;;
        esac
    done

    if [[ "$cur" == -* ]]; then
        case "$subcommand" in
            run)
                COMPREPLY=($(compgen -W "--workspace --model --base-url --resume --permission --format --help" -- "$cur"))
                ;;
            chat)
                COMPREPLY=($(compgen -W "--workspace --help" -- "$cur"))
                ;;
            sessions)
                COMPREPLY=($(compgen -W "--workspace --export --help" -- "$cur"))
                ;;
            *)
                COMPREPLY=($(compgen -W "--help --version" -- "$cur"))
                ;;
        esac
        return 0
    fi

    # Complete subcommand names
    if [[ -z "$subcommand" ]]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return 0
    fi
}

complete -F _mythic_completions mythic
