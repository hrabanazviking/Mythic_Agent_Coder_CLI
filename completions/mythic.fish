# fish completion for mythic
# Install: copy to ~/.config/fish/completions/mythic.fish

# Subcommands
complete -c mythic -f -n __fish_use_subcommand -a run -d 'Run one task'
complete -c mythic -f -n __fish_use_subcommand -a chat -d 'Start terminal chat'
complete -c mythic -f -n __fish_use_subcommand -a tui -d 'Start Textual interface'
complete -c mythic -f -n __fish_use_subcommand -a sessions -d 'List/export sessions'

# Global flags
complete -c mythic -s h -l help -d 'Show help'
complete -c mythic -l version -d 'Show version'

# run flags
complete -c mythic -n '__fish_seen_subcommand_from run' -l workspace -d 'Project directory' -r -F
complete -c mythic -n '__fish_seen_subcommand_from run' -l model -d 'Model override' -r
complete -c mythic -n '__fish_seen_subcommand_from run' -l base-url -d 'Endpoint override' -r
complete -c mythic -n '__fish_seen_subcommand_from run' -l resume -d 'Resume session' -r
complete -c mythic -n '__fish_seen_subcommand_from run' -l permission -d 'Permission mode' -r -a 'read-only ask trusted'
complete -c mythic -n '__fish_seen_subcommand_from run' -l format -d 'Output format' -r -a 'plain json jsonl'

# chat flags
complete -c mythic -n '__fish_seen_subcommand_from chat' -l workspace -d 'Project directory' -r -F

# sessions flags
complete -c mythic -n '__fish_seen_subcommand_from sessions' -l workspace -d 'Project directory' -r -F
complete -c mythic -n '__fish_seen_subcommand_from sessions' -l export -d 'Export transcript' -r
