/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_002f3ea0(int param_1,undefined4 param_2,undefined1 *param_3)

{
  int *piVar1;
  int iVar2;
  undefined4 uVar3;
  int iVar4;
  
  piVar1 = (int *)FUN_0032b664();
  piVar1 = (int *)(**(code **)(*piVar1 + 0x30))();
  iVar2 = *(int *)(param_1 + 4);
  if ((((*(int *)(iVar2 + 0x60) == 0) && (iVar4 = *(int *)(iVar2 + 100), iVar4 != -1)) &&
      (iVar2 = FUN_00317c48(iVar2,iVar4), iVar2 != 0)) &&
     (iVar2 = (**(code **)(*piVar1 + 100))(piVar1,param_2,iVar4,0xd), iVar2 != 0)) {
    iVar2 = *piVar1;
    *param_3 = 1;
    uVar3 = (**(code **)(iVar2 + 0x40))(piVar1,param_2,iVar4,0xd,0xffffffff);
  }
  else {
    *param_3 = 0;
    piVar1 = (int *)FUN_0032b664(param_1);
    piVar1 = (int *)(**(code **)(*piVar1 + 0x10))(piVar1,param_2);
    if ((piVar1 == (int *)0x0) ||
       (piVar1 = (int *)(**(code **)(*piVar1 + 0x30))(), piVar1 == (int *)0x0)) {
      uVar3 = 0;
    }
    else {
      uVar3 = (**(code **)(*piVar1 + 0x14))();
    }
  }
  return uVar3;
}

