/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_001e8220(int param_1,int *param_2)

{
  int iVar1;
  int iVar2;
  uint uVar3;
  int *piVar4;
  int iVar5;
  int local_28;
  undefined1 auStack_24 [8];
  
  if ((param_2 != (int *)0x0) && (((uint)param_2 & 3) == 0)) {
    iVar2 = *(int *)(*param_2 + -0xc);
    uVar3 = (int)param_2 + iVar2;
    if ((uVar3 != 0) && (((uVar3 & 3) == 0 && (*(int *)((int)param_2 + iVar2) == 0x5e715e28)))) {
      (**(code **)(*param_2 + 0x14))(auStack_24);
      iVar1 = *(int *)(param_1 + 0x1c);
      iVar2 = 0;
      if (0 < iVar1) {
        do {
          piVar4 = *(int **)(*(int *)(param_1 + 0x14) + iVar2 * 4);
          iVar2 = iVar2 + 1;
          if (piVar4 != (int *)0x0) {
            FUN_00627ba0(&local_28,auStack_24);
            iVar1 = local_28;
            iVar5 = piVar4[1];
            FUN_006280c8(&local_28);
            if (iVar5 == iVar1) {
              FUN_006280c8(auStack_24);
              (**(code **)(*piVar4 + 0x10))(piVar4,param_2);
              return;
            }
            iVar1 = *(int *)(param_1 + 0x1c);
          }
        } while (iVar2 < iVar1);
      }
      FUN_006280c8(auStack_24);
      return;
    }
  }
  FUN_004f782c(DAT_001e8308,DAT_001e830c,DAT_001e8310);
  return;
}

