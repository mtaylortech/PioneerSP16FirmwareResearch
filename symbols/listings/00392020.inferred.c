/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int * FUN_00392020(int param_1,undefined4 param_2)

{
  bool bVar1;
  int iVar2;
  uint uVar3;
  int *piVar4;
  uint uVar5;
  int *piVar6;
  int iVar7;
  int local_30 [3];
  
  uVar3 = *(uint *)(param_1 + 0x94);
  if (0 < (int)uVar3) {
    uVar5 = 0;
    do {
      if ((uVar5 < uVar3) &&
         (piVar6 = *(int **)(*(int *)(param_1 + 0x8c) + uVar5 * 4), piVar6 != (int *)0x0)) {
        piVar4 = piVar6 + 0x1d;
        DataMemoryBarrier(0xf);
        do {
          bVar1 = (bool)hasExclusiveAccess(piVar4);
        } while (!bVar1);
        *piVar4 = *piVar4 + 1;
        DataMemoryBarrier(0xf);
        DataMemoryBarrier(0xf);
        do {
          iVar2 = *piVar4;
          bVar1 = (bool)hasExclusiveAccess(piVar4);
        } while (!bVar1);
        *piVar4 = iVar2 + -1;
        DataMemoryBarrier(0xf);
        if (iVar2 + -1 == 0) {
          (**(code **)(*piVar6 + 4))(piVar6);
        }
        FUN_00627ba0(local_30,param_2);
        iVar2 = local_30[0];
        iVar7 = piVar6[0x21];
        FUN_006280c8(local_30);
        if (iVar7 == iVar2) {
          return piVar6;
        }
        uVar3 = *(uint *)(param_1 + 0x94);
      }
      uVar5 = uVar5 + 1;
    } while ((int)uVar5 < (int)uVar3);
  }
  return (int *)0x0;
}

