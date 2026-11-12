/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_0055b1a4(int param_1,undefined4 param_2,undefined1 param_3,undefined4 param_4)

{
  *(undefined4 *)(param_1 + 8) = param_2;
  *(undefined1 *)(param_1 + 0xc) = param_3;
  *(undefined1 *)(param_1 + 0xd) = param_3;
  *(undefined1 *)(param_1 + 0xe) = param_3;
  if (*(int **)(param_1 + 0x18) != (int *)0x0) {
    (**(code **)(**(int **)(param_1 + 0x18) + 4))();
    *(undefined4 *)(param_1 + 0x18) = 0;
  }
  *(undefined4 *)(param_1 + 0x18) = param_4;
  *(undefined4 *)(param_1 + 0x10) = 0;
  *(bool *)(param_1 + 0xf) = *(int *)(param_1 + 0x14) != 0;
  *(undefined1 *)(param_1 + 4) = 1;
  return;
}

