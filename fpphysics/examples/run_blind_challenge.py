from fpphysics.blind_protocol import run_default_blind_challenge, write_blind_challenge

run = run_default_blind_challenge(include_lab=True)
paths = write_blind_challenge(run, "blind_challenge_run")
print(paths)
print(run.summary)
