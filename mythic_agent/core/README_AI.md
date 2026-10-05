# Core services

Bootstrap/configuration, internal events and shared runtime contracts live here.
Do not import optional UI/audio modules for core startup. Keep network/tool work
outside state locks. Use `INTERFACE.md` for outcome/settings/event contracts.
Configuration reads preserve original data; explicit saves are private/atomic.
Workspace sessions use leases and transactional checkpoints; raw transcripts stay
separate from selected context. Redact exports and diagnostics. Owned I/O belongs
in execution.py; drain cancellation cleanup before returning. Permission checks
must precede effects. Managed secondary-agent lifecycle is S08.
