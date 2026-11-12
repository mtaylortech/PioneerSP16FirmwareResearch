/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0026b404(int param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int *piVar1;
  code *pcVar2;
  
  piVar1 = *(int **)(*(int *)(param_1 + 8) + 0x10);
  pcVar2 = *(code **)(*piVar1 + 8);
  (*pcVar2)(piVar1,&DAT_00f542a4,param_3,pcVar2,param_4);
  return;
}

