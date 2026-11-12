/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int * candidate_00806858(int *param_1)

{
  bool bVar1;
  int iVar2;
  int *piVar3;
  int *piVar4;
  int iVar5;
  int unaff_r4;
  
  if ((int *)(*(int *)(unaff_r4 + 0x1c) + 3000U) < param_1) {
    FUN_00697918();
    piVar3 = (int *)(unaff_r4 + 0x18);
    iVar5 = *_UNK_00806894;
    iVar2 = *piVar3;
    if (iVar5 != iVar2) {
      if (iVar5 != 0) {
        piVar4 = (int *)(iVar5 + 4);
        DataMemoryBarrier(0xf);
        do {
          bVar1 = (bool)hasExclusiveAccess(piVar4);
        } while (!bVar1);
        *piVar4 = *piVar4 + 1;
        DataMemoryBarrier(0xf);
        iVar2 = *piVar3;
      }
      *piVar3 = iVar5;
      FUN_0071da04(iVar2);
    }
    return piVar3;
  }
  return param_1;
}

