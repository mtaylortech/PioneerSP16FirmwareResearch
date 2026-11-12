/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_004a1ab8(int param_1,short *param_2)

{
  undefined1 uVar1;
  short sVar2;
  char cVar3;
  int iVar4;
  int iVar5;
  char *pcVar6;
  char cVar7;
  int iVar8;
  uint in_fpscr;
  float fVar9;
  float fVar10;
  
  pcVar6 = *(char **)(param_2 + 0x10);
  cVar3 = *pcVar6;
  if (*(char *)(param_1 + 0x110) == cVar3) {
    iVar8 = *(int *)(pcVar6 + 4);
    if (*(int *)(param_1 + 0x114) != iVar8) {
      iVar5 = *(int *)(pcVar6 + 8);
      iVar4 = *(int *)(pcVar6 + 0xc);
      cVar7 = pcVar6[0x10];
      goto LAB_004a1af0;
    }
    iVar5 = *(int *)(pcVar6 + 8);
    if (*(int *)(param_1 + 0x118) != iVar5) {
      iVar4 = *(int *)(pcVar6 + 0xc);
      cVar7 = pcVar6[0x10];
      goto LAB_004a1af0;
    }
    iVar4 = *(int *)(pcVar6 + 0xc);
    cVar7 = pcVar6[0x10];
    if (*(int *)(param_1 + 0x11c) != iVar4) goto LAB_004a1af0;
    if (*(char *)(param_1 + 0x120) != cVar7) goto LAB_004a1af0;
    iVar8 = FUN_0062e318(param_1 + 0x124,pcVar6 + 0x14);
    if ((iVar8 == 0) || (*(int *)(param_1 + 0x128) != *(int *)(pcVar6 + 0x18))) {
      cVar3 = *pcVar6;
      iVar8 = *(int *)(pcVar6 + 4);
      iVar5 = *(int *)(pcVar6 + 8);
      iVar4 = *(int *)(pcVar6 + 0xc);
      cVar7 = pcVar6[0x10];
      goto LAB_004a1af0;
    }
  }
  else {
    iVar8 = *(int *)(pcVar6 + 4);
    iVar5 = *(int *)(pcVar6 + 8);
    iVar4 = *(int *)(pcVar6 + 0xc);
    cVar7 = pcVar6[0x10];
LAB_004a1af0:
    *(char *)(param_1 + 0x110) = cVar3;
    *(int *)(param_1 + 0x118) = iVar5;
    *(int *)(param_1 + 0x114) = iVar8;
    *(int *)(param_1 + 0x11c) = iVar4;
    *(char *)(param_1 + 0x120) = cVar7;
    FUN_0062ab80(param_1 + 0x124,pcVar6 + 0x14);
    *(undefined4 *)(param_1 + 0x128) = *(undefined4 *)(pcVar6 + 0x18);
    FUN_004a1798(param_1,0);
  }
  pcVar6 = *(char **)(param_2 + 0xe);
  cVar3 = *pcVar6;
  if (*(char *)(param_1 + 0xf4) == cVar3) {
    iVar8 = *(int *)(pcVar6 + 4);
    if (*(int *)(param_1 + 0xf8) != iVar8) {
      iVar5 = *(int *)(pcVar6 + 8);
      iVar4 = *(int *)(pcVar6 + 0xc);
      cVar7 = pcVar6[0x10];
      goto LAB_004a1b50;
    }
    iVar5 = *(int *)(pcVar6 + 8);
    if (*(int *)(param_1 + 0xfc) != iVar5) {
      iVar4 = *(int *)(pcVar6 + 0xc);
      cVar7 = pcVar6[0x10];
      goto LAB_004a1b50;
    }
    iVar4 = *(int *)(pcVar6 + 0xc);
    cVar7 = pcVar6[0x10];
    if (*(int *)(param_1 + 0x100) != iVar4) goto LAB_004a1b50;
    if (*(char *)(param_1 + 0x104) != cVar7) goto LAB_004a1b50;
    iVar8 = FUN_0062e318(param_1 + 0x108,pcVar6 + 0x14);
    if ((iVar8 == 0) || (*(int *)(param_1 + 0x10c) != *(int *)(pcVar6 + 0x18))) {
      cVar3 = *pcVar6;
      iVar8 = *(int *)(pcVar6 + 4);
      iVar5 = *(int *)(pcVar6 + 8);
      iVar4 = *(int *)(pcVar6 + 0xc);
      cVar7 = pcVar6[0x10];
      goto LAB_004a1b50;
    }
  }
  else {
    iVar8 = *(int *)(pcVar6 + 4);
    iVar5 = *(int *)(pcVar6 + 8);
    iVar4 = *(int *)(pcVar6 + 0xc);
    cVar7 = pcVar6[0x10];
LAB_004a1b50:
    *(char *)(param_1 + 0xf4) = cVar3;
    *(int *)(param_1 + 0xfc) = iVar5;
    *(int *)(param_1 + 0xf8) = iVar8;
    *(int *)(param_1 + 0x100) = iVar4;
    *(char *)(param_1 + 0x104) = cVar7;
    FUN_0062ab80(param_1 + 0x108,pcVar6 + 0x14);
    *(undefined4 *)(param_1 + 0x10c) = *(undefined4 *)(pcVar6 + 0x18);
    FUN_004a1798(param_1,1);
  }
  FUN_0039dafc(*(undefined4 *)(param_1 + 0xcc),*(undefined4 *)(param_2 + 4),
               *(undefined4 *)(param_2 + 6));
  FUN_0039dafc(*(undefined4 *)(param_1 + 0xd0),*(undefined4 *)(param_2 + 8),
               *(undefined4 *)(param_2 + 10));
  pcVar6 = *(char **)(param_2 + 0xc);
  cVar3 = *pcVar6;
  if (*(char *)(param_1 + 0xd8) == cVar3) {
    iVar8 = *(int *)(pcVar6 + 4);
    if (*(int *)(param_1 + 0xdc) == iVar8) {
      iVar4 = *(int *)(pcVar6 + 8);
      if (*(int *)(param_1 + 0xe0) == iVar4) {
        iVar5 = *(int *)(pcVar6 + 0xc);
        cVar7 = pcVar6[0x10];
        if (*(int *)(param_1 + 0xe4) == iVar5) {
          if (*(char *)(param_1 + 0xe8) == cVar7) {
            iVar8 = FUN_0062e318(param_1 + 0xec,pcVar6 + 0x14);
            if ((iVar8 != 0) && (*(int *)(param_1 + 0xf0) == *(int *)(pcVar6 + 0x18)))
            goto LAB_004a1c3c;
            cVar3 = *pcVar6;
            iVar8 = *(int *)(pcVar6 + 4);
            iVar4 = *(int *)(pcVar6 + 8);
            iVar5 = *(int *)(pcVar6 + 0xc);
            cVar7 = pcVar6[0x10];
          }
        }
      }
      else {
        iVar5 = *(int *)(pcVar6 + 0xc);
        cVar7 = pcVar6[0x10];
      }
    }
    else {
      iVar4 = *(int *)(pcVar6 + 8);
      iVar5 = *(int *)(pcVar6 + 0xc);
      cVar7 = pcVar6[0x10];
    }
  }
  else {
    iVar8 = *(int *)(pcVar6 + 4);
    iVar4 = *(int *)(pcVar6 + 8);
    iVar5 = *(int *)(pcVar6 + 0xc);
    cVar7 = pcVar6[0x10];
  }
  *(char *)(param_1 + 0xd8) = cVar3;
  *(int *)(param_1 + 0xe0) = iVar4;
  *(int *)(param_1 + 0xe4) = iVar5;
  *(int *)(param_1 + 0xdc) = iVar8;
  *(char *)(param_1 + 0xe8) = cVar7;
  FUN_0062ab80(param_1 + 0xec,pcVar6 + 0x14);
  iVar8 = *(int *)(pcVar6 + 8);
  iVar4 = *(int *)(pcVar6 + 4);
  fVar9 = (float)VectorSignedToFloat(*(undefined4 *)(pcVar6 + 0xc),(byte)(in_fpscr >> 0x16) & 3);
  *(undefined4 *)(param_1 + 0xf0) = *(undefined4 *)(pcVar6 + 0x18);
  fVar10 = (float)VectorSignedToFloat(iVar8 - iVar4,(byte)(in_fpscr >> 0x16) & 3);
  FUN_0079c798(*(undefined4 *)(param_1 + 200),*(undefined4 *)(param_1 + 0xd4),
               0xf7 - (int)((fVar9 / fVar10) * DAT_004a1ee0));
LAB_004a1c3c:
  if ((*param_2 != *(short *)(param_1 + 300)) ||
     (*(int *)(param_2 + 2) != *(int *)(param_1 + 0x130))) {
    sVar2 = *param_2;
    uVar1 = *(undefined1 *)((int)param_2 + 1);
    *(int *)(param_1 + 0x130) = *(int *)(param_2 + 2);
    *(char *)(param_1 + 300) = (char)sVar2;
    *(undefined1 *)(param_1 + 0x12d) = uVar1;
    FUN_004a19e0(param_1);
  }
  FUN_0038e824(*(undefined4 *)(param_1 + 0xb8),*(undefined1 *)((int)param_2 + 0x25));
  FUN_0038e824(*(undefined4 *)(param_1 + 0xc0),*(undefined1 *)((int)param_2 + 0x25));
  if (*(char *)(param_1 + 0x134) == (char)param_2[0x12]) {
    return;
  }
  *(char *)(param_1 + 0x134) = (char)param_2[0x12];
  FUN_00790630(param_1);
  return;
}

