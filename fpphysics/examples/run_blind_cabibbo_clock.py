from fpphysics.blind_cabibbo import run_cabibbo_clock_blind_challenge, write_cabibbo_clock_run

if __name__ == "__main__":
    run = run_cabibbo_clock_blind_challenge()
    paths = write_cabibbo_clock_run(run, "cabibbo_clock_blind_run")
    print(run["summary"])
    print(paths)
