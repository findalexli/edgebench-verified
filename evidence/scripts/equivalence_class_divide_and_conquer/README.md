Rerun (one container at a time; image already pulled by digest):
  python3 -I gen_crafted.py crafted            && ./run_crafted.sh      # crafted star n=1e6 cases A-E
  python3 -I random_oracle.py gen random_cases 400 && ./run_random.sh > random_results.txt \
     && python3 -I random_oracle.py check random_cases random_results.txt   # 329 small brute-force cases
  ./run_official.sh                                                        # 30 official T3 inputs, std + naive
  python3 -I make_instrumented.py checker_original.cpp checker_true_cost.cpp  # regenerate instrumented copy
Saved outputs: run_crafted_output.txt, random_results.txt, official_results.txt, strictness_output.txt.
Note: run_*.sh use --memory 4g/2g as written; the coordinator later capped containers at 2g.
