"""Multi-block responses (after make_responses.py; argv[1] = response dir). One model output holding
two fenced JSON blocks, as a model might print a draft and then a revision.
  N  A's block (complete, 77) followed by D's block (A without R009, incomplete) in ONE output
  O  D's block followed by A's block in ONE output (control: the last block is the complete one)
  P  A's block followed by a truncated, unparseable JSON block (first 400 characters of A's JSON)"""
import os, sys
out = sys.argv[1]
rd = lambda n: open(os.path.join(out, n + ".txt"), encoding="utf-8").read()
A, D = rd("A_complete_one_deduction_each"), rd("D_A_minus_R009")
for name, body in (("N_A_block_then_D_block_one_output", "Draft assessment:\n" + A + "\nRevised assessment:\n" + D),
                   ("O_D_block_then_A_block_one_output", "Draft assessment:\n" + D + "\nRevised assessment:\n" + A),
                   ("P_A_block_then_truncated_block_one_output", "Draft assessment:\n" + A + "\nRevised assessment:\n```json\n" + A.split("```json\n", 1)[1][:400] + "\n```\n")):
    with open(os.path.join(out, name + ".txt"), "w", encoding="utf-8") as f:
        f.write(body)
