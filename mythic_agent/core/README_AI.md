# Core services

Bootstrap/configuration, internal events and shared runtime contracts live here.
Do not import optional UI/audio modules for core startup. Keep network/tool work
outside state locks. Use `INTERFACE.md` for outcome/settings/event contracts.
Portable configuration and active-I/O cancellation are upcoming roadmap owners.
