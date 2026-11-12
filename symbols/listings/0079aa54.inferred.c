/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

int FUN_0079aa54(void)

{
  char cVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  int *piVar5;
  int iVar6;
  int iVar7;
  int iVar8;
  int iVar9;
  uint uVar10;
  
  iVar9 = DAT_0079ac54;
  iVar3 = *(int *)(DAT_0079ac54 + 100);
  if (*(int *)(DAT_0079ac54 + 100) == 0) {
    iVar3 = FUN_00780f34();
    if (iVar3 == 0) {
      if (*(char *)(iVar9 + 0x140) != '\0') {
        iVar3 = FUN_0078ca5c();
        uVar10 = *(int *)(iVar3 + 0x44) - 1;
        iVar9 = uVar10 * 4;
        for (; -1 < (int)uVar10; uVar10 = uVar10 - 1) {
          if (uVar10 < *(uint *)(iVar3 + 0x44)) {
            uVar4 = *(undefined4 *)(*(int *)(iVar3 + 0x3c) + iVar9);
          }
          else {
            uVar4 = 0;
          }
          iVar2 = FUN_0078ddc8(uVar4);
          if (iVar2 != 0) {
            iVar6 = *(int *)(iVar2 + 0x20);
            iVar8 = *(int *)(iVar2 + 4);
            if (iVar6 != 0) {
              iVar7 = *(int *)(iVar6 + 8);
              do {
                if (iVar7 == 0) goto LAB_0079ac40;
                iVar7 = *(int *)(iVar7 + 0xc);
              } while (iVar8 != iVar7);
              iVar6 = *(int *)(iVar6 + 8);
              do {
                if ((*(byte *)(iVar6 + 0x68) & 2) == 0) goto LAB_0079ac40;
                iVar6 = *(int *)(iVar6 + 0xc);
              } while (iVar6 != 0);
              piVar5 = (int *)FUN_0078ddc8();
              if ((piVar5 == (int *)0x0) ||
                 (cVar1 = (**(code **)(*piVar5 + 0x38))(), cVar1 == '\x01')) {
                iVar8 = *(int *)(iVar2 + 4);
              }
              else {
                if (*(int *)(iVar2 + 0x20) == 0) goto LAB_0079ac14;
                iVar8 = *(int *)(*(int *)(iVar2 + 0x20) + 8);
              }
            }
LAB_0079ac40:
            for (; iVar8 != 0; iVar8 = *(int *)(iVar8 + 0xc)) {
              iVar2 = __dynamic_cast(iVar8,DAT_0079ac58,DAT_0079ac60,0xfffffffe);
              if (iVar2 != 0) {
                return iVar2;
              }
            }
          }
LAB_0079ac14:
          iVar9 = iVar9 + -4;
        }
      }
      goto LAB_0079aaec;
    }
    FUN_0078ddc8();
    iVar9 = FUN_0079a9b0();
    if (iVar9 != 0) {
      iVar3 = iVar9;
    }
  }
  iVar2 = __dynamic_cast(iVar3,DAT_0079ac58,DAT_0079ac5c,0);
  iVar9 = iVar3;
  if (((iVar2 != 0) && (*(int *)(iVar2 + 0x7c) != 0)) &&
     (iVar9 = *(int *)(*(int *)(iVar2 + 0x7c) + 8), iVar9 == 0)) {
    iVar9 = iVar3;
  }
  iVar3 = __dynamic_cast(iVar9,DAT_0079ac58,DAT_0079ac60,0xfffffffe);
  if (iVar3 != 0) {
    return iVar3;
  }
  for (iVar9 = *(int *)(iVar9 + 0xc); iVar9 != 0; iVar9 = *(int *)(iVar9 + 0xc)) {
    iVar3 = __dynamic_cast(iVar9,DAT_0079ac58,DAT_0079ac60,0xfffffffe);
    if (iVar3 != 0) {
      return iVar3;
    }
  }
LAB_0079aaec:
  if (*DAT_0079ac64 != 0) {
    iVar9 = __dynamic_cast(*DAT_0079ac64,DAT_0079ac68,DAT_0079ac6c,0);
    if (iVar9 != 0) {
      iVar9 = iVar9 + 0x10;
    }
    return iVar9;
  }
  return 0;
}

