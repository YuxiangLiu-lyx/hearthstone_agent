"""Exact fallback acceptance evidence, without claiming a final paired study."""
import collections
import json
from pathlib import Path
import time
from development.secret_hunter_astra_sprint.study import ROOT, RUN, ZIP_SHA, BASE_SHA, ANCHOR
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_program.common import quantiles, sha


def protocol_evidence(acceptance):
    summaries = {}
    for mode in ('luna', 'client'):
        records = [r for r in acceptance['records'] if r['mode'] == mode]
        internal, publication, residual = [], [], []
        for record in records:
            player = Path(record['game_path']) / f"p{record['seat']}"
            decisions_path = player / 'seat/scratch/decisions.jsonl'
            calls_path = player / 'seat/mcp_calls.jsonl'
            decisions = [json.loads(line) for line in decisions_path.read_text().splitlines()]
            normal = {d['seq']: d for d in decisions if d['phase'] != 'deck_submission'}
            calls = [json.loads(line) for line in calls_path.read_text().splitlines()]
            internal.extend(d['elapsed_s'] for d in normal.values())
            timestamps = []
            for call in calls:
                if call['tool'] != 'act' or call['arguments']['seq'] not in normal:
                    continue
                seq = call['arguments']['seq']
                state_path = player / f'decisions/{seq:05d}.state.json'
                published = state_path.stat().st_mtime
                elapsed = call['time'] - published
                publication.append(elapsed)
                residual.append(elapsed - normal[seq]['elapsed_s'])
                timestamps.append({'seq': seq, 'state_published_unix': published,
                                   'act_unix': call['time'], 'internal_program_s': normal[seq]['elapsed_s'],
                                   'state_sha256': sha(state_path)})
            chain, sessions = [], {}
            command_counts, tool_counts = collections.Counter(), collections.Counter()
            if mode == 'luna':
                for transcript in sorted((player / 'seat').glob('session_*.jsonl')):
                    sessions[transcript.name] = sha(transcript)
                    for line in transcript.read_text().splitlines():
                        event = json.loads(line)
                        if event.get('type') != 'item.completed':
                            continue
                        item = event.get('item', {})
                        if item.get('type') == 'command_execution':
                            command = item.get('command', '')
                            assert command == "/bin/zsh -c 'python scripts/decide.py'", command
                            envelope = json.loads(item['aggregated_output'])
                            chain.append({'kind': 'script', 'command': command, 'envelope': envelope})
                            command_counts[command] += 1
                        if item.get('type') == 'mcp_tool_call':
                            tool = item.get('tool')
                            assert tool in ('wait', 'act'), tool
                            chain.append({'kind': 'mcp', 'tool': tool, 'arguments': item.get('arguments'),
                                          'terminal_seen': 'GAME OVER' in json.dumps(item.get('result', {}))})
                            tool_counts[tool] += 1
            proof = {'key': record['key'], 'source_sha256': record['source_sha256'],
                     'script_decisions_sha256': sha(decisions_path), 'mcp_calls_sha256': sha(calls_path),
                     'session_hashes_only': sessions, 'tool_chain': chain, 'timing_samples': timestamps,
                     'command_counts': dict(command_counts), 'tool_counts': dict(tool_counts),
                     'scope': 'Only script envelopes and permitted MCP calls are exported from model sessions. No model reasoning, authentication files, or full session transcripts.'}
            ledger.atomic(RUN / 'relay-proof' / (record['key'] + '.json'), proof)
        summaries[mode] = {'games': len(records), 'act_calls': sum(r['act_calls'] for r in records),
                           'actual_first_games': sum(r['result']['first_player'] == r['seat'] for r in records),
                           'envelope_mismatches': sum(r['envelope_mismatches'] for r in records),
                           'ordinary_fallbacks': sum(r['ordinary_fallbacks'] for r in records),
                           'internal_program_latency_s': quantiles(internal),
                           'publication_to_act_latency_s': quantiles(publication),
                           'outside_internal_program_latency_s': quantiles(residual)}
    return summaries


def main():
    acceptance = json.loads((RUN / 'fallback-acceptance.json').read_text())
    assert acceptance['passed'] and acceptance['source_sha256'] == BASE_SHA
    assert sha(RUN / 'frozen/DARCL2.zip') == ZIP_SHA
    runtime_path = ROOT / 'docs/secret_hunter_astra_sprint/runtime-DARCL2-loaded.json'
    runtime = json.loads(runtime_path.read_text())
    db = ledger.connect(RUN)
    rows = [json.loads(r[0]) for r in db.execute("select result from tasks where candidate='DARCL2' and status='done'")]
    execution = {'completed_full_cli_games': len(rows),
                 'latency_s': quantiles([t for r in rows for t in r['decision_times']]),
                 'over_2s': sum(r.get('over_2s', 0) for r in rows),
                 'ordinary_fallbacks': sum(r.get('fallbacks', 0) for r in rows),
                 'policy_errors': sum(len(r.get('policy_errors', [])) for r in rows),
                 'scope': 'Execution checks only across completed development and pilot games, including the retained partial confirmation. No aggregate win-rate claim and no inspection of confirmation outcomes.'}
    result = {'created': time.time(), 'artifact_role': 'Original fallback acceptance before strategy selection',
              'zip_sha256': ZIP_SHA, 'source_sha256': BASE_SHA, 'source_anchor_commit': ANCHOR,
              'exact_path': runtime['candidate'], 'deck_audit': json.loads((RUN / 'fallback-deck-audit.json').read_text()),
              'protocol_passed': True, 'relay': protocol_evidence(acceptance),
              'runtime_sha256': sha(runtime_path), 'runtime': {k: v for k, v in runtime.items() if k != 'records'},
              'full_cli_execution': execution, 'paired_final_validation_complete': False,
              'limitations': ['DA2 confirmation is checkpointed and incomplete; selection and final seeds remain unopened.',
                             'Loaded-host concurrency-3 actions match cold actions on all 16 inputs, but concurrency-6 differs on two. Preserve this failed stability check.',
                             'No new formal course result or Astra gain is claimed.'],
              'timing_scope': 'Full CLI includes Python process startup. Relay internal timer excludes interpreter startup. State publication to MCP act includes model, shell, Python, and transport; it is not pure network latency. Quantiles are pooled from raw samples.'}
    ledger.atomic(RUN / 'fallback-validation.json', result)
    ledger.atomic(ROOT / 'docs/secret_hunter_astra_sprint/fallback-validation.json', result)
    print(json.dumps({'protocol_passed': True, 'relay': result['relay'], 'full_cli_execution': execution}, indent=2))


if __name__ == '__main__':
    main()
