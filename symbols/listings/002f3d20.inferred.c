/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_002f3d20(int param_1,undefined4 *param_2,int *param_3)

{
  int *piVar1;
  undefined4 uVar2;
  undefined4 local_18;
  int iStack_14;
  
  uVar2 = *(undefined4 *)(*(int *)(param_1 + 4) + 0x54);
  piVar1 = (int *)FUN_0032b664();
  piVar1 = (int *)(**(code **)(*piVar1 + 0x10))(piVar1,uVar2);
  if ((piVar1 != (int *)0x0) &&
     (piVar1 = (int *)(**(code **)(*piVar1 + 0x30))(), piVar1 != (int *)0x0)) {
    (**(code **)(*piVar1 + 0x20))(&local_18,piVar1,0);
    *param_2 = local_18;
    *param_3 = iStack_14 + -1;
  }
  return;
}

