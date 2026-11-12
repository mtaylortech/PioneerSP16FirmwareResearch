/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void candidate_00753670(int param_1)

{
  if (*(int **)(param_1 + 0xc) == (int *)0x0) {
    return;
  }
  (**(code **)(**(int **)(param_1 + 0xc) + 0x74))();
  return;
}

