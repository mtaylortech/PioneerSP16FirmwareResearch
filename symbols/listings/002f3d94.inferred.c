/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_002f3d94(int param_1,undefined1 *param_2)

{
  int *piVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  
  piVar1 = (int *)FUN_0032b664();
  piVar1 = (int *)(**(code **)(*piVar1 + 0x30))();
  iVar2 = *(int *)(param_1 + 4);
  uVar4 = *(undefined4 *)(iVar2 + 0x54);
  if ((*(int *)(iVar2 + 0x60) == 0) && (iVar3 = *(int *)(iVar2 + 100), iVar3 != -1)) {
    iVar2 = FUN_00317c48(iVar2,iVar3);
    if ((iVar2 != 0) && (iVar2 = (**(code **)(*piVar1 + 100))(piVar1,uVar4,iVar3,0xd), iVar2 != 0))
    {
      iVar2 = *piVar1;
      *param_2 = 1;
      uVar4 = (**(code **)(iVar2 + 0x40))(piVar1,uVar4,iVar3,0xd,0xffffffff);
      return uVar4;
    }
    iVar2 = *(int *)(param_1 + 4);
  }
  *param_2 = 0;
  uVar4 = *(undefined4 *)(iVar2 + 0x54);
  piVar1 = (int *)FUN_0032b664(param_1);
  piVar1 = (int *)(**(code **)(*piVar1 + 0x10))(piVar1,uVar4);
  if ((piVar1 == (int *)0x0) ||
     (piVar1 = (int *)(**(code **)(*piVar1 + 0x30))(), piVar1 == (int *)0x0)) {
    uVar4 = 0;
  }
  else {
    uVar4 = (**(code **)(*piVar1 + 0x14))();
  }
  return uVar4;
}

