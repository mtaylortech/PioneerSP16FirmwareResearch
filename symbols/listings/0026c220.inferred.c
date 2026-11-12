/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void candidate_0026c220(int param_1)

{
  char cVar1;
  byte bVar2;
  int *piVar3;
  undefined1 uVar4;
  int iVar5;
  int iVar6;
  undefined4 uVar7;
  int iVar8;
  int iVar9;
  undefined4 uVar10;
  undefined4 uVar11;
  uint uVar12;
  uint uVar13;
  uint uVar14;
  code *pcVar15;
  int iVar16;
  int iVar17;
  int *piVar18;
  uint uVar19;
  undefined4 uVar20;
  bool bVar21;
  undefined4 uStack_2d4;
  undefined1 auStack_2d0 [8];
  undefined1 auStack_2c8 [4];
  undefined1 auStack_2c4 [4];
  undefined1 auStack_2c0 [4];
  undefined1 auStack_2bc [8];
  int aiStack_2b4 [154];
  undefined4 uStack_4c;
  undefined4 uStack_48;
  undefined4 uStack_44;
  undefined4 uStack_40;
  undefined4 uStack_3c;
  undefined4 uStack_38;
  undefined4 uStack_34;
  undefined4 uStack_30;
  byte *apbStack_2c [2];
  
  piVar18 = DAT_0026c20c;
  if (*(char *)(*(int *)(param_1 + 0x24) + 0x4316) != '\0') {
    return;
  }
  iVar16 = param_1 + 0x20;
  iVar17 = *DAT_0026c20c;
  iVar5 = FUN_002fb130(iVar16);
  piVar3 = DAT_0026c210;
  if (iVar17 != iVar5) {
    *piVar18 = iVar5;
    piVar3 = DAT_0026c210;
    *(undefined1 *)(param_1 + 0x6a8) = 0;
  }
  iVar17 = *piVar3;
  iVar5 = FUN_002f32e8(iVar16);
  if (iVar17 != iVar5) {
    *piVar3 = iVar5;
  }
  if (iVar17 != iVar5) {
    *(undefined1 *)(param_1 + 0x6a8) = 0;
  }
  FUN_0026bb70(param_1,&uStack_4c,&uStack_48,&uStack_44,&uStack_40);
  piVar18 = aiStack_2b4;
  FUN_0026bbf4(param_1,&uStack_3c,&uStack_38,&uStack_34,&uStack_30);
  iVar5 = 0;
  iVar17 = param_1;
  do {
    iVar9 = FUN_002f3bd0(iVar16,iVar5);
    if (iVar9 == 0) {
      FUN_002f36f0(apbStack_2c,iVar16,iVar5);
      bVar2 = *apbStack_2c[0];
      uVar14 = (uint)bVar2;
      if ((bVar2 & 0x80) != 0) {
        if ((bVar2 & 0x40) == 0) {
          uVar14 = uVar14 & 0x7f;
        }
        else {
          uVar13 = 0x40;
          uVar12 = 0x7f;
          uVar19 = 0;
          do {
            uVar13 = uVar13 >> 1;
            uVar12 = uVar12 >> 1;
            uVar19 = uVar19 + 1;
          } while (0x10 < uVar13 && (uVar13 & uVar14) != 0);
          uVar14 = uVar12 & uVar14;
          if ((uVar19 != 0) && (uVar13 = (uint)apbStack_2c[0][1], (uVar13 & 0xc0) == 0x80)) {
            uVar12 = 1;
            do {
              uVar12 = uVar12 + 1;
              uVar14 = uVar13 & 0x3f | uVar14 << 6;
              if (uVar19 < uVar12) break;
              uVar13 = (uint)apbStack_2c[0][uVar12];
            } while ((uVar13 & 0xc0) == 0x80);
          }
        }
      }
      bVar21 = uVar14 != 0;
      FUN_00627f38(apbStack_2c);
    }
    else {
      bVar21 = true;
      if (iVar9 != 1) {
        bVar21 = false;
      }
    }
    *(bool *)(piVar18 + -7) = bVar21;
    uVar4 = FUN_002f3aec(iVar16,iVar5);
    *(undefined1 *)((int)piVar18 + -0x1b) = uVar4;
    iVar6 = FUN_002f35b0(iVar16,iVar5);
    iVar9 = iVar5 * 0x28;
    piVar18[-6] = iVar6;
    FUN_0026bae8(param_1,iVar5,auStack_2d0 + iVar9 + 8,auStack_2c4 + iVar9,
                 auStack_2d0 + iVar9 + 0x10,auStack_2bc + iVar9);
    iVar9 = FUN_002f32e8(iVar16);
    if (iVar5 == iVar9) {
      iVar9 = iVar5 * 8;
      uVar7 = FUN_002f3ea0(iVar16,iVar5,param_1 + iVar5 * 0x1c + 0x168);
      *(undefined4 *)(iVar17 + 0x174) = uVar7;
    }
    else {
      *(undefined1 *)(iVar17 + 0x168) = 0;
      iVar9 = iVar5 << 3;
      uVar7 = FUN_002f3fa0(iVar16,iVar5);
      *(undefined4 *)(iVar17 + 0x174) = uVar7;
    }
    iVar6 = (iVar9 - iVar5) * 4;
    piVar18[-1] = param_1 + iVar6 + 0x168;
    iVar8 = FUN_002f32e8(iVar16);
    if (iVar5 == iVar8) {
      uVar7 = FUN_002f4228(iVar16,iVar5,param_1 + iVar6 + 0x328);
      *(undefined4 *)(iVar17 + 0x334) = uVar7;
    }
    else {
      *(undefined1 *)(iVar17 + 0x328) = 0;
      uVar7 = FUN_002f4328(iVar16,iVar5);
      *(undefined4 *)(iVar17 + 0x334) = uVar7;
    }
    iVar6 = (iVar9 - iVar5) * 4;
    *piVar18 = param_1 + iVar6 + 0x328;
    iVar8 = FUN_002f32e8(iVar16);
    if (iVar5 == iVar8) {
      uVar7 = FUN_002f5f88(iVar16,iVar5,param_1 + iVar6 + 0x4e8);
      *(undefined4 *)(iVar17 + 0x4f4) = uVar7;
    }
    else {
      *(undefined1 *)(iVar17 + 0x4e8) = 0;
      uVar7 = FUN_002f6088(iVar16,iVar5);
      *(undefined4 *)(iVar17 + 0x4f4) = uVar7;
    }
    cVar1 = *(char *)(param_1 + 0x6a8);
    piVar18[1] = param_1 + (iVar9 - iVar5) * 4 + 0x4e8;
    bVar21 = false;
    if (cVar1 != '\0') {
      iVar9 = FUN_002f32e8(iVar16);
      bVar21 = iVar5 == iVar9;
    }
    *(bool *)(piVar18 + 2) = bVar21;
    iVar9 = FUN_002f32e8(iVar16);
    iVar17 = iVar17 + 0x1c;
    iVar6 = iVar5 + 1;
    *(bool *)((int)piVar18 + 9) = iVar5 == iVar9;
    piVar18 = piVar18 + 10;
    iVar5 = iVar6;
    if (iVar6 == 0x10) {
      uVar7 = *(undefined4 *)(param_1 + 0x128);
      iVar5 = FUN_002fdf7c(iVar16);
      uVar14 = FUN_002fe010(iVar16);
      if (uVar14 < 0x14) {
        uVar20 = *(undefined4 *)(DAT_0026c214 + uVar14 * 4 + 0x238);
      }
      else {
        uVar20 = 0xffffffff;
      }
      uVar10 = FUN_002f32e8(iVar16);
      uVar11 = FUN_002f62c0(iVar16);
      pcVar15 = *(code **)(**(int **)(param_1 + 0x6ac) + 0x2c);
      *(undefined4 *)(param_1 + 0x13c) = uVar11;
      iVar17 = (*pcVar15)(*(int **)(param_1 + 0x6ac));
      if (iVar17 == 0) {
        uStack_2d4 = 0xffffffff;
      }
      else {
        uStack_2d4 = (**(code **)(**(int **)(param_1 + 0x6ac) + 0x34))();
      }
      uVar11 = FUN_002f6384(iVar16);
      *(undefined4 *)(param_1 + 0x158) = uVar11;
      FUN_0044c23c(uVar7,iVar5 != 0,uVar20,uVar10,uStack_4c,uStack_48,uStack_44,uStack_40,
                   param_1 + 0x130,uStack_3c,uStack_38,uStack_34,uStack_30,uStack_2d4,
                   param_1 + 0x14c,auStack_2d0);
      return;
    }
  } while( true );
}

