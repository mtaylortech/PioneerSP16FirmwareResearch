/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_00817cf0(int *param_1)

{
  int iVar1;
  int *piVar2;
  int *piVar3;
  int *piVar4;
  int iVar5;
  int local_18;
  undefined1 auStack_14 [8];
  
  iVar5 = param_1[4];
  if (iVar5 == 0) {
    if (*param_1 == 0xb) {
      memcpy(DAT_00817dec,param_1 + 5,0x20);
    }
  }
  else {
    local_18 = 0;
    FUN_00697ecc(auStack_14);
    iVar1 = XFindContext(*DAT_00817df0,iVar5,*DAT_00817df4,&local_18);
    iVar5 = local_18;
    if ((iVar1 == 0) && (local_18 != 0)) {
      iVar1 = FUN_0078ca5c();
      piVar4 = *(int **)(iVar1 + 0x48);
      piVar2 = piVar4 + *(int *)(iVar1 + 0x50);
      if (piVar4 == piVar2) {
LAB_00817db4:
        local_18 = 0;
        FUN_00697eec(auStack_14);
        return;
      }
      iVar1 = *piVar4;
      piVar3 = piVar4;
      while (iVar5 != iVar1) {
        piVar4 = piVar4 + 1;
        if (piVar2 == piVar4) goto LAB_00817db4;
        piVar3 = piVar3 + 1;
        iVar1 = *piVar3;
      }
    }
    iVar5 = local_18;
    FUN_00697eec(auStack_14);
    if (iVar5 != 0) {
      FUN_00817564(iVar5,param_1);
    }
  }
  return;
}

