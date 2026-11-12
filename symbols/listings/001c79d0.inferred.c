/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void candidate_001c79d0(undefined8 *param_1,int param_2,int param_3)

{
  undefined4 uVar1;
  
  if (param_3 == 1) {
    uVar1 = *(undefined4 *)(*(int *)(param_2 + 0x8c) + 0x18);
    *(undefined4 *)param_1 = *(undefined4 *)(*(int *)(param_2 + 0x8c) + 0x14);
    *(undefined4 *)((int)param_1 + 4) = uVar1;
    return;
  }
  if (param_3 != 2) {
    if (param_3 == 0) {
      uVar1 = *(undefined4 *)(*(int *)(param_2 + 0x90) + 0x18);
      *(undefined4 *)param_1 = *(undefined4 *)(*(int *)(param_2 + 0x90) + 0x14);
      *(undefined4 *)((int)param_1 + 4) = uVar1;
      return;
    }
    *param_1 = DAT_001c7a38;
    return;
  }
  uVar1 = *(undefined4 *)(*(int *)(param_2 + 0x94) + 0x18);
  *(undefined4 *)param_1 = *(undefined4 *)(*(int *)(param_2 + 0x94) + 0x14);
  *(undefined4 *)((int)param_1 + 4) = uVar1;
  return;
}

