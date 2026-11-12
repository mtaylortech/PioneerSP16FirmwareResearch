/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_001c7928(int param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  code *pcVar1;
  
  pcVar1 = *(code **)(**(int **)(param_1 + 0x14) + 0x108);
  (*pcVar1)(*(int **)(param_1 + 0x14),*(undefined4 *)(param_1 + 0x1c),
            *(undefined4 *)(param_1 + 0x18),pcVar1,param_4);
  return;
}

