/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void candidate_002bff00(int *param_1,undefined4 param_2)

{
  if (*(char *)(param_1[9] + 0x4316) == '\0') {
    switch(param_2) {
    case 0:
      (**(code **)(*param_1 + 0x60))();
      return;
    case 1:
      (**(code **)(*param_1 + 100))();
      return;
    case 2:
      (**(code **)(*param_1 + 0x68))();
      return;
    case 3:
      (**(code **)(*param_1 + 0x6c))();
      return;
    case 4:
      (**(code **)(*param_1 + 0x70))();
      return;
    case 5:
      (**(code **)(*param_1 + 0x74))();
      return;
    case 6:
      (**(code **)(*param_1 + 0x78))();
    }
    return;
  }
  return;
}

