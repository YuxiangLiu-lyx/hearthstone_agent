# Runtime contract and timing boundary

The artifact is one ZIP/one skill root, name secret-hunter-agent, Python scripts
and course dependencies only. Model Luna is gpt-6-luna with medium effort in the
actual SkillSeat/loader. Each fresh game gets its own copied skill, game/ and
scratch/. Setup is an explicit MCP deck_submission; the host never reads deck.json
automatically. Choice means Tracking, separate from main. Draws score as losses
outside ladder; forfeits remain in our outcome denominator.

SkillSeat launches the one main Codex model and its MCP server. ClientSeat instead
exports HS_ARENA_MCP to a plain program. Pure Python benchmarks call the official
runner and observe player views directly, without either model or MCP. Only real
SkillSeat games establish the submitted runtime/model behavior. Neither the course
engine nor its timer was modified. Custom research scheduling merely supplies the
same frozen opponents to the official play_game and SkillSeat classes.

Course prompt explicitly restricts the player to its own working folder. SkillSeat
places the mailbox outside that folder and passes its command to Codex as MCP
configuration; it does not export a script connection or give the skill a supported
API for submitting through the existing connection. Reading sibling mailbox/config
files or writing protocol files directly is not an allowed workaround. The real
skill helper records has_client_mcp_env=false. The main model's connected act tool
is therefore the unique submitter. A portable supervisor with independent act is
NOT implemented or claimed. This blocks the requested unconditional guarantee when
the main model does not return, including initial deck_submission before any script.

The budget layer computes publication = deadline_epoch_s - timeout_s and converts
deadline/adoption/target to monotonic timestamps on each invocation. Repeated tools
use that same publication, so wait/deep calls cannot reset the window. Default
worker hard cap is two seconds; ordinary-tool ceiling five and deep ceiling ten;
bounded lethal loops use much less. The parent subprocess.run timeout kills and
reaps its worker. No worker calls a model or spawns descendants. Deadline-short
states immediately use a current legal phase-specific fallback.

The 40-second window controls acceptance of model suggestions by the selector.
It does not cancel the model, force it to invoke the selector, or force an MCP call.
The 90-second target/30-second official reserve likewise cannot constrain a stalled
hosted generation. Late model choices are discarded *if the selector is reached*.
Never kill the main course model to rescue a deadline: early exit forfeits.

Timing checks include worker hang/crash, malformed action/index, old seq, duplicate
selection, a new game sharing seq, short remaining deadline, missing suggestion,
successive seq changes and game_over. They prove local tool/acceptance behavior,
not independent submission. Real model transcripts separately expose deviations
from the requested prepare/select/act workflow, and these remain release blockers
until corrected. Current strict-timing classification: research-only.
