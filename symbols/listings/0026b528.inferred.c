/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void candidate_0026b528(int param_1,int param_2,int *param_3)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [4];
  
  iVar2 = DAT_0026b6a0;
  iVar3 = DAT_0026b69c;
  if (*(int *)(param_1 + 0x6b0) == param_2) {
    if (*param_3 == 0) {
      if (0 < *(int *)(param_1 + 0x6b8)) {
        iVar2 = 0;
        do {
          iVar1 = FUN_0062e318(iVar3 + iVar2 * 4,param_3 + 2);
          if (iVar1 != 0) {
            iVar2 = iVar2 + param_3[1];
            if (iVar2 < 0) {
              iVar2 = 0;
            }
            else {
              iVar1 = *(int *)(param_1 + 0x6b8) + -1;
              if (iVar1 <= iVar2) {
                iVar2 = iVar1;
              }
            }
            uVar4 = *(undefined4 *)(param_1 + 0x6b0);
            iVar1 = *param_3;
            FUN_0062ab18(auStack_20,iVar3 + iVar2 * 4);
            FUN_001efe84(uVar4,iVar1,auStack_20);
            FUN_00627f38(auStack_20);
            return;
          }
          iVar2 = iVar2 + 1;
        } while (iVar2 < *(int *)(param_1 + 0x6b8));
      }
    }
    else if ((*param_3 == 1) && (0 < *(int *)(param_1 + 0x6bc))) {
      iVar3 = 0;
      do {
        iVar1 = FUN_0062e318(iVar2 + iVar3 * 4,param_3 + 2);
        if (iVar1 != 0) {
          iVar3 = iVar3 + param_3[1];
          if (iVar3 < 0) {
            iVar3 = 0;
          }
          else {
            iVar1 = *(int *)(param_1 + 0x6bc) + -1;
            if (iVar1 <= iVar3) {
              iVar3 = iVar1;
            }
          }
          uVar4 = *(undefined4 *)(param_1 + 0x6b0);
          iVar1 = *param_3;
          FUN_0062ab18(auStack_1c,iVar2 + iVar3 * 4);
          FUN_001efe84(uVar4,iVar1,auStack_1c);
          FUN_00627f38(auStack_1c);
          return;
        }
        iVar3 = iVar3 + 1;
      } while (iVar3 < *(int *)(param_1 + 0x6bc));
    }
  }
  return;
}

