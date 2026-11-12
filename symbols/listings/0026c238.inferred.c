/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0026c238(int param_1)

{
  byte bVar1;
  undefined1 uVar2;
  int iVar3;
  undefined4 uVar4;
  int iVar5;
  int iVar6;
  undefined4 uVar7;
  undefined4 uVar8;
  undefined4 uVar9;
  uint uVar10;
  uint uVar11;
  uint uVar12;
  code *pcVar13;
  int iVar14;
  int iVar15;
  int *piVar16;
  uint uVar17;
  int iVar18;
  undefined4 uVar19;
  bool bVar20;
  undefined1 local_2d0 [8];
  undefined1 auStack_2c8 [4];
  undefined1 auStack_2c4 [4];
  undefined1 auStack_2c0 [4];
  undefined1 auStack_2bc [12];
  int local_2b0 [153];
  undefined4 local_4c;
  undefined4 uStack_48;
  undefined4 uStack_44;
  undefined4 local_40;
  undefined4 local_3c;
  undefined4 local_38;
  undefined4 local_34;
  undefined4 local_30;
  byte *local_2c [2];
  
  iVar14 = 0;
  FUN_0026bb70(param_1,&local_4c,&uStack_48,&uStack_44,&local_40);
  piVar16 = local_2b0;
  iVar15 = param_1 + 0x20;
  FUN_0026bbf4(param_1,&local_3c,&local_38,&local_34,&local_30);
  iVar18 = param_1;
  do {
    iVar6 = FUN_002f3bd0(iVar15,iVar14);
    if (iVar6 == 0) {
      FUN_002f36f0(local_2c,iVar15,iVar14);
      bVar1 = *local_2c[0];
      uVar12 = (uint)bVar1;
      if ((bVar1 & 0x80) != 0) {
        if ((bVar1 & 0x40) == 0) {
          uVar12 = uVar12 & 0x7f;
        }
        else {
          uVar11 = 0x40;
          uVar10 = 0x7f;
          uVar17 = 0;
          do {
            uVar11 = uVar11 >> 1;
            uVar10 = uVar10 >> 1;
            uVar17 = uVar17 + 1;
          } while (0x10 < uVar11 && (uVar11 & uVar12) != 0);
          uVar12 = uVar10 & uVar12;
          if ((uVar17 != 0) && (uVar11 = (uint)local_2c[0][1], (uVar11 & 0xc0) == 0x80)) {
            uVar10 = 1;
            do {
              uVar10 = uVar10 + 1;
              uVar12 = uVar11 & 0x3f | uVar12 << 6;
              if (uVar17 < uVar10) break;
              uVar11 = (uint)local_2c[0][uVar10];
            } while ((uVar11 & 0xc0) == 0x80);
          }
        }
      }
      bVar20 = uVar12 != 0;
      FUN_00627f38(local_2c);
    }
    else {
      bVar20 = true;
      if (iVar6 != 1) {
        bVar20 = false;
      }
    }
    *(bool *)(piVar16 + -8) = bVar20;
    uVar2 = FUN_002f3aec(iVar15,iVar14);
    *(undefined1 *)((int)piVar16 + -0x1f) = uVar2;
    iVar3 = FUN_002f35b0(iVar15,iVar14);
    iVar6 = iVar14 * 0x28;
    piVar16[-7] = iVar3;
    FUN_0026bae8(param_1,iVar14,local_2d0 + iVar6 + 8,auStack_2c4 + iVar6,local_2d0 + iVar6 + 0x10,
                 auStack_2bc + iVar6);
    iVar6 = FUN_002f32e8(iVar15);
    if (iVar14 == iVar6) {
      iVar6 = iVar14 * 8;
      uVar4 = FUN_002f3ea0(iVar15,iVar14,param_1 + iVar14 * 0x1c + 0x168);
      *(undefined4 *)(iVar18 + 0x174) = uVar4;
    }
    else {
      *(undefined1 *)(iVar18 + 0x168) = 0;
      iVar6 = iVar14 << 3;
      uVar4 = FUN_002f3fa0(iVar15,iVar14);
      *(undefined4 *)(iVar18 + 0x174) = uVar4;
    }
    iVar3 = (iVar6 - iVar14) * 4;
    piVar16[-2] = param_1 + iVar3 + 0x168;
    iVar5 = FUN_002f32e8(iVar15);
    if (iVar14 == iVar5) {
      uVar4 = FUN_002f4228(iVar15,iVar14,param_1 + iVar3 + 0x328);
      *(undefined4 *)(iVar18 + 0x334) = uVar4;
    }
    else {
      *(undefined1 *)(iVar18 + 0x328) = 0;
      uVar4 = FUN_002f4328(iVar15,iVar14);
      *(undefined4 *)(iVar18 + 0x334) = uVar4;
    }
    iVar3 = (iVar6 - iVar14) * 4;
    piVar16[-1] = param_1 + iVar3 + 0x328;
    iVar5 = FUN_002f32e8(iVar15);
    if (iVar14 == iVar5) {
      uVar4 = FUN_002f5f88(iVar15,iVar14,param_1 + iVar3 + 0x4e8);
      *(undefined4 *)(iVar18 + 0x4f4) = uVar4;
    }
    else {
      *(undefined1 *)(iVar18 + 0x4e8) = 0;
      uVar4 = FUN_002f6088(iVar15,iVar14);
      *(undefined4 *)(iVar18 + 0x4f4) = uVar4;
    }
    iVar6 = iVar6 - iVar14;
    iVar14 = iVar14 + 1;
    *(undefined1 *)(piVar16 + 1) = 0;
    iVar18 = iVar18 + 0x1c;
    *piVar16 = param_1 + iVar6 * 4 + 0x4e8;
    piVar16 = piVar16 + 10;
    if (iVar14 == 0x10) {
      uVar4 = *(undefined4 *)(param_1 + 0x128);
      iVar18 = FUN_002fdf7c(iVar15);
      uVar12 = FUN_002fe010(iVar15);
      if (uVar12 < 0x14) {
        uVar19 = *(undefined4 *)(DAT_0026c648 + uVar12 * 4 + 0x238);
      }
      else {
        uVar19 = 0xffffffff;
      }
      uVar7 = FUN_002f32e8(iVar15);
      uVar8 = FUN_002f62c0(iVar15);
      pcVar13 = *(code **)(**(int **)(param_1 + 0x6ac) + 0x2c);
      *(undefined4 *)(param_1 + 0x13c) = uVar8;
      iVar14 = (*pcVar13)(*(int **)(param_1 + 0x6ac));
      if (iVar14 == 0) {
        uVar8 = 0xffffffff;
      }
      else {
        uVar8 = (**(code **)(**(int **)(param_1 + 0x6ac) + 0x34))();
      }
      uVar9 = FUN_002f6384(iVar15);
      *(undefined4 *)(param_1 + 0x158) = uVar9;
      FUN_0044c6c4(uVar4,iVar18 != 0,uVar19,uVar7,local_4c,uStack_48,uStack_44,local_40,
                   param_1 + 0x130,local_3c,local_38,local_34,local_30,uVar8,param_1 + 0x14c,
                   local_2d0);
      *(undefined1 *)(param_1 + 0x6a8) = 0;
      FUN_0069bf5c(param_1 + 0x114,0x32);
      return;
    }
  } while( true );
}

