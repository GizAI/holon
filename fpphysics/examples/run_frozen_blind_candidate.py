from fpphysics.frozen_blind_candidate import write_frozen_candidate_outputs

if __name__ == "__main__":
    paths = write_frozen_candidate_outputs("frozen_candidate_run")
    for key, value in paths.items():
        print(f"{key}: {value}")
