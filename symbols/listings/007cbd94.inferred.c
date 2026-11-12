/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_007cbd94(int param_1,int param_2,uint param_3)

{
  int iVar1;
  int *piVar2;
  int iVar3;
  int *piVar4;
  uint uVar5;
  byte bVar6;
  int *piVar7;
  void *__src;
  undefined8 local_38;
  undefined8 local_30;
  undefined1 auStack_28 [16];
  
  iVar1 = *(int *)(param_2 + 0xc);
  if (iVar1 != param_1) {
    if (iVar1 == 0) {
      bVar6 = *(byte *)(param_2 + 0x68);
      if ((bVar6 & 1) != 0) {
        FUN_007c227c(param_2);
        bVar6 = *(byte *)(param_2 + 0x68);
      }
    }
    else {
      piVar2 = *(int **)(iVar1 + 0x28);
      if (piVar2 == piVar2 + *(int *)(iVar1 + 0x30)) {
LAB_007cbe00:
        iVar3 = -1;
      }
      else {
        piVar4 = piVar2;
        piVar7 = piVar2;
        if (param_2 == *piVar2) {
          iVar3 = 0;
        }
        else {
          do {
            piVar7 = piVar7 + 1;
            if (piVar2 + *(int *)(iVar1 + 0x30) == piVar7) goto LAB_007cbe00;
            piVar4 = piVar4 + 1;
          } while (param_2 != *piVar4);
          iVar3 = (int)piVar7 - (int)piVar2 >> 2;
        }
      }
      FUN_007c1324(iVar1,iVar3,1,1);
      bVar6 = *(byte *)(param_2 + 0x68);
    }
    *(int *)(param_2 + 0xc) = param_1;
    if (((bVar6 & 2) != 0) && (param_1 != 0)) {
      local_30 = *(undefined8 *)(param_2 + 0x18);
      local_38 = 0;
      FUN_0078f660(auStack_28,param_2,&local_38);
      FUN_0078fb14(param_1,auStack_28);
    }
    uVar5 = *(uint *)(param_1 + 0x30);
    if ((*(byte *)(param_2 + 0x69) & 1) == 0) {
      if (((int)param_3 < 0) || ((int)uVar5 < (int)param_3)) {
        param_3 = uVar5;
      }
      if (0 < (int)param_3) {
        iVar1 = (param_3 - 1) * 4;
        do {
          piVar2 = (int *)(*(int *)(param_1 + 0x28) + iVar1);
          iVar1 = iVar1 + -4;
          if ((*(byte *)(*piVar2 + 0x69) & 1) == 0) break;
          param_3 = param_3 - 1;
        } while (param_3 != 0);
      }
    }
    iVar1 = uVar5 + 1;
    if (*(int *)(param_1 + 0x2c) < iVar1) {
      FUN_0080b4dc(param_1 + 0x28,iVar1 + iVar1 / 2 + 8U & 0xfffffff8);
      uVar5 = *(uint *)(param_1 + 0x30);
    }
    if (param_3 < uVar5) {
      iVar1 = *(int *)(param_1 + 0x28);
      __src = (void *)(iVar1 + param_3 * 4);
      if (0 < (int)(uVar5 - param_3)) {
        memmove((void *)((int)__src + 4),__src,(uVar5 - param_3) * 4);
      }
      iVar3 = *(int *)(param_1 + 0x30);
      if (__src != (void *)0x0) {
        *(int *)(iVar1 + param_3 * 4) = param_2;
      }
      *(int *)(param_1 + 0x30) = iVar3 + 1;
    }
    else {
      *(uint *)(param_1 + 0x30) = uVar5 + 1;
      if (*(int *)(param_1 + 0x28) + uVar5 * 4 != 0) {
        *(int *)(*(int *)(param_1 + 0x28) + uVar5 * 4) = param_2;
      }
    }
    FUN_007894fc(param_2);
    FUN_00789604(param_1);
  }
  return;
}

