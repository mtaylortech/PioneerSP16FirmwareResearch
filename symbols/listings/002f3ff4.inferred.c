/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_002f3ff4(int param_1,undefined4 param_2)

{
  int *piVar1;
  int iVar2;
  undefined4 uVar3;
  
  iVar2 = *(int *)(param_1 + 4);
  uVar3 = *(undefined4 *)(iVar2 + 0x54);
  if ((*(int *)(iVar2 + 0x60) == 0) && (iVar2 = *(int *)(iVar2 + 100), iVar2 != -1)) {
    piVar1 = (int *)FUN_0032b664();
    piVar1 = (int *)(**(code **)(*piVar1 + 0x30))();
    (**(code **)(*piVar1 + 0x2c))(piVar1,uVar3,iVar2,0xd,param_2,0);
  }
  else {
    piVar1 = (int *)FUN_0032b664(param_1);
    piVar1 = (int *)(**(code **)(*piVar1 + 0x10))(piVar1,uVar3);
    if ((piVar1 != (int *)0x0) &&
       (piVar1 = (int *)(**(code **)(*piVar1 + 0x30))(), piVar1 != (int *)0x0)) {
      (**(code **)(*piVar1 + 8))(piVar1,param_2,0);
    }
  }
  return;
}

