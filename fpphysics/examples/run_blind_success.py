from fpphysics.blind_success import run_blind_success_challenge, write_blind_success

run = run_blind_success_challenge()
paths = write_blind_success(run, "blind_success_run")
print(run["summary"])
print(paths)
