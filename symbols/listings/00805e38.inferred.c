/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_00805e38(int param_1)

{
  byte *pbVar1;
  byte *pbVar2;
  byte bVar3;
  int iVar4;
  undefined4 *puVar5;
  void *pvVar6;
  uint *puVar7;
  int *piVar8;
  int iVar9;
  uint uVar10;
  undefined4 uVar11;
  int iVar12;
  int iVar13;
  int iVar14;
  uint uVar15;
  int *piVar16;
  byte *pbVar17;
  int iVar18;
  uint uVar19;
  size_t __size;
  undefined4 uVar20;
  int iVar21;
  uint uVar22;
  int iVar23;
  uint uVar24;
  undefined4 uVar25;
  uint uVar26;
  bool bVar27;
  uint local_150;
  uint local_14c;
  uint local_148;
  uint local_144;
  uint local_140;
  uint local_13c;
  int local_130;
  int local_120;
  int local_11c;
  int local_118;
  undefined4 local_ec;
  undefined4 local_e8;
  int local_e4;
  int local_e0;
  int local_a8;
  int local_9c;
  int local_90 [2];
  int local_88;
  int local_84;
  int local_70;
  int local_6c;
  undefined8 local_68;
  int *local_60;
  undefined4 local_5c;
  int local_58;
  int *local_50;
  int local_4c;
  int local_48;
  undefined8 local_40;
  undefined1 auStack_38 [4];
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [8];
  
  local_60 = (int *)0x0;
  local_5c = 0;
  local_58 = 0;
  FUN_004ff510(param_1 + 0x20,&local_60);
  if (local_58 < 2) {
    if (local_58 == 0) goto LAB_00806724;
    local_120 = *local_60;
    iVar14 = local_60[2];
    iVar18 = local_60[3];
    local_11c = local_60[1];
  }
  else {
    local_120 = *local_60;
    local_11c = local_60[1];
    iVar14 = local_120 + local_60[2];
    iVar4 = local_58 << 4;
    iVar12 = local_58;
    iVar18 = local_11c + local_60[3];
    while( true ) {
      iVar12 = iVar12 + -1;
      iVar9 = iVar4 + -0x10;
      if (iVar12 == 0) break;
      iVar21 = *(int *)((int)local_60 + iVar9);
      iVar23 = *(int *)((int)local_60 + iVar4 + -0xc);
      if (iVar21 <= local_120) {
        local_120 = iVar21;
      }
      if (iVar23 <= local_11c) {
        local_11c = iVar23;
      }
      iVar21 = iVar21 + *(int *)((int)local_60 + iVar4 + -8);
      iVar23 = iVar23 + *(int *)((int)local_60 + iVar4 + -4);
      if (iVar14 < iVar21) {
        iVar14 = iVar21;
      }
      iVar4 = iVar9;
      if (iVar18 < iVar23) {
        iVar18 = iVar23;
      }
    }
    iVar14 = iVar14 - local_120;
    iVar18 = iVar18 - local_11c;
  }
  if ((iVar14 < 1) || (iVar18 < 1)) goto LAB_00806724;
  if (*(int *)(param_1 + 0x18) == 0) {
LAB_00805f34:
    puVar5 = operator_new(0x4c);
    uVar15 = iVar14 + 0x1fU & 0xffffffe0;
    uVar19 = iVar18 + 0x1fU & 0xffffffe0;
    uVar20 = *(undefined4 *)(*(int *)(param_1 + 0x14) + 0x5c);
    iVar4 = *(int *)(*(int *)(param_1 + 0x14) + 0x58);
    FUN_006d2f0c(puVar5,1,uVar15,uVar19);
    uVar11 = DAT_00806838;
    puVar5[0xd] = 0;
    puVar5[0xe] = 0;
    puVar5[0x12] = 0;
    *puVar5 = uVar11;
    puVar5[0xc] = uVar20;
    puVar5[0xf] = 3;
    puVar5[0x10] = uVar15 * 3;
    FUN_00697ecc(auStack_2c);
    iVar14 = puVar5[0x10];
    free((void *)puVar5[0xd]);
    pvVar6 = malloc(iVar14 * uVar19);
    puVar5[0xd] = pvVar6;
    puVar5[0x11] = pvVar6;
    puVar7 = calloc(1,0x58);
    iVar12 = puVar5[0xc];
    iVar14 = puVar5[0xf];
    iVar18 = *DAT_0080683c;
    uVar22 = puVar5[0x10];
    uVar10 = *(uint *)(iVar18 + 0x30);
    uVar24 = *(uint *)(iVar18 + 0x34);
    uVar26 = *(uint *)(iVar18 + 0x3c);
    puVar5[0xb] = puVar7;
    puVar7[2] = 0;
    *puVar7 = uVar15;
    puVar7[1] = uVar19;
    puVar7[3] = 2;
    puVar7[4] = (uint)pvVar6;
    puVar7[8] = 0x20;
    puVar7[5] = uVar10;
    puVar7[0xc] = 0xff0000;
    puVar7[6] = uVar24;
    puVar7[0xd] = 0xff00;
    puVar7[7] = uVar26;
    puVar7[9] = iVar14 << 3;
    puVar7[10] = uVar22;
    puVar7[0xb] = iVar14 << 3;
    puVar7[0xe] = 0xff;
    if (iVar12 == 0x10) {
      free((void *)puVar5[0xe]);
      pvVar6 = malloc(uVar15 * 2 * uVar19);
      uVar25 = *(undefined4 *)(iVar4 + 0xc);
      uVar11 = *(undefined4 *)(iVar4 + 0x10);
      uVar20 = *(undefined4 *)(iVar4 + 0x14);
      iVar14 = puVar5[0xb];
      puVar5[0xe] = pvVar6;
      *(void **)(iVar14 + 0x10) = pvVar6;
      *(undefined4 *)(iVar14 + 0x20) = 0x10;
      *(undefined4 *)(iVar14 + 0x24) = 0x10;
      *(uint *)(iVar14 + 0x28) = uVar15 * 2;
      *(undefined4 *)(iVar14 + 0x2c) = 0x10;
      *(undefined4 *)(iVar14 + 0x30) = uVar25;
      *(undefined4 *)(iVar14 + 0x34) = uVar11;
      *(undefined4 *)(iVar14 + 0x38) = uVar20;
    }
    XInitImage();
    FUN_00697eec(auStack_2c);
    FUN_006d3154(auStack_38,puVar5);
    FUN_006d3310(param_1 + 0x18,auStack_38);
    FUN_00707778(auStack_38);
  }
  else {
    iVar4 = FUN_006d3360(param_1 + 0x18);
    if ((iVar4 < iVar14) || (iVar4 = FUN_006d3370(param_1 + 0x18), iVar4 < iVar18))
    goto LAB_00805f34;
  }
  FUN_0069bf5c(param_1,10);
  iVar14 = local_58;
  iVar18 = 0;
  local_50 = (int *)0x0;
  local_4c = 0;
  local_48 = local_58;
  if (local_58 == 0) {
    __size = 0;
  }
  else {
    __size = local_58 << 4;
    if (local_58 < 1) {
      local_4c = local_58;
    }
    else {
      local_50 = malloc(__size);
      local_4c = iVar14;
      piVar8 = local_50;
      do {
        if (piVar8 != (int *)0x0) {
          *piVar8 = local_60[iVar18 * 4];
          piVar8[1] = local_60[iVar18 * 4 + 1];
          piVar8[2] = local_60[iVar18 * 4 + 2];
          piVar8[3] = local_60[iVar18 * 4 + 3];
        }
        iVar18 = iVar18 + 1;
        piVar8 = piVar8 + 4;
      } while (iVar18 != iVar14);
    }
  }
  for (piVar8 = local_50; (int *)((int)local_50 + __size) != piVar8; piVar8 = piVar8 + 4) {
    *piVar8 = *piVar8 - local_120;
    piVar8[1] = piVar8[1] - local_11c;
  }
  iVar14 = *(int *)(param_1 + 0x14);
  if ((*(int *)(iVar14 + 0x5c) == 0x20) &&
     (piVar16 = (int *)((int)local_60 + __size), piVar8 = local_60, local_60 != piVar16)) {
    do {
      local_68 = *(undefined8 *)(piVar8 + 2);
      local_6c = piVar8[1] - local_11c;
      local_70 = *piVar8 - local_120;
      FUN_006c16fc(auStack_34,0);
      FUN_0070a3b8(param_1 + 0x18,&local_70,auStack_34);
      piVar8 = piVar8 + 4;
      FUN_006a0280(auStack_34);
    } while (piVar8 != piVar16);
    iVar14 = *(int *)(param_1 + 0x14);
  }
  piVar8 = (int *)FUN_007ac33c(*(undefined4 *)(iVar14 + 4));
  local_40 = FloatVectorNeg(CONCAT44(local_11c,local_120),1,4);
  piVar8 = (int *)(**(code **)(*piVar8 + 0x2c))(piVar8,param_1 + 0x18,&local_40,&local_50);
  FUN_00789bc0(*(undefined4 *)(param_1 + 0x14),piVar8);
  if (piVar8 != (int *)0x0) {
    (**(code **)(*piVar8 + 4))(piVar8);
  }
  piVar16 = local_60 + local_58 * 4;
  for (piVar8 = local_60; piVar8 != piVar16; piVar8 = piVar8 + 4) {
    local_118 = piVar8[2];
    iVar14 = __aeabi_idiv(0xc80,local_118);
    local_130 = piVar8[1];
    iVar18 = local_130 + piVar8[3];
    if (iVar14 < 1) {
      iVar14 = 1;
    }
    if (local_130 < iVar18) {
      do {
        iVar9 = *piVar8;
        iVar12 = *(int *)(param_1 + 0x18);
        uVar11 = *(undefined4 *)(*(int *)(param_1 + 0x14) + 0x38);
        FUN_00697ecc(auStack_2c);
        iVar4 = *(int *)(iVar12 + 0x48);
        if (iVar4 == 0) {
          local_ec = 3;
          local_e8 = 0xffffffff;
          local_e4 = iVar4;
          local_e0 = iVar4;
          local_a8 = iVar4;
          local_9c = iVar4;
          iVar4 = XCreateGC(DAT_00f6e684,uVar11,0x9000f,&local_ec);
          *(int *)(iVar12 + 0x48) = iVar4;
        }
        iVar23 = iVar14;
        if (iVar18 - local_130 <= iVar14) {
          iVar23 = iVar18 - local_130;
        }
        iVar18 = iVar9 - local_120;
        iVar21 = local_130 - local_11c;
        if (*(int *)(iVar12 + 0x30) == 0x10) {
          iVar4 = *(int *)(iVar12 + 0x2c);
          uVar22 = *(uint *)(iVar4 + 0x30);
          uVar19 = *(uint *)(iVar4 + 0x38);
          uVar24 = *(uint *)(iVar4 + 0x34);
          uVar10 = 0x20;
          uVar15 = 0x1f;
          do {
            if ((uVar22 >> (uVar15 & 0xff) & 1) != 0) {
              local_150 = uVar10 - 8 & ~((int)(uVar10 - 8) >> 0x1f);
              goto LAB_008063d0;
            }
            bVar27 = uVar15 != 0;
            uVar10 = uVar15;
            uVar15 = uVar15 - 1;
          } while (bVar27);
          local_150 = 0;
LAB_008063d0:
          uVar10 = 0x20;
          uVar15 = 0x1f;
          do {
            if ((uVar22 >> (uVar15 & 0xff) & 1) != 0) {
              local_14c = 8 - uVar10 & ~((int)(8 - uVar10) >> 0x1f);
              goto LAB_0080640c;
            }
            bVar27 = uVar15 != 0;
            uVar10 = uVar15;
            uVar15 = uVar15 - 1;
          } while (bVar27);
          local_14c = 0;
LAB_0080640c:
          uVar10 = 0x20;
          uVar15 = 0x1f;
          do {
            if ((uVar24 >> (uVar15 & 0xff) & 1) != 0) {
              local_148 = uVar10 - 8 & ~((int)(uVar10 - 8) >> 0x1f);
              goto LAB_00806444;
            }
            bVar27 = uVar15 != 0;
            uVar10 = uVar15;
            uVar15 = uVar15 - 1;
          } while (bVar27);
          local_148 = 0;
LAB_00806444:
          uVar10 = 0x20;
          uVar15 = 0x1f;
          do {
            if ((uVar24 >> (uVar15 & 0xff) & 1) != 0) {
              local_144 = 8 - uVar10 & ~((int)(8 - uVar10) >> 0x1f);
              goto LAB_0080647c;
            }
            bVar27 = uVar15 != 0;
            uVar10 = uVar15;
            uVar15 = uVar15 - 1;
          } while (bVar27);
          local_144 = 0;
LAB_0080647c:
          uVar10 = 0x20;
          uVar15 = 0x1f;
          do {
            if ((uVar19 >> (uVar15 & 0xff) & 1) != 0) {
              local_140 = uVar10 - 8 & ~((int)(uVar10 - 8) >> 0x1f);
              goto LAB_008064b4;
            }
            bVar27 = uVar15 != 0;
            uVar10 = uVar15;
            uVar15 = uVar15 - 1;
          } while (bVar27);
          local_140 = 0;
LAB_008064b4:
          uVar10 = 0x20;
          uVar15 = 0x1f;
          do {
            if ((uVar19 >> (uVar15 & 0xff) & 1) != 0) {
              local_13c = 8 - uVar10 & ~((int)(8 - uVar10) >> 0x1f);
              goto LAB_008064ec;
            }
            bVar27 = uVar15 != 0;
            uVar10 = uVar15;
            uVar15 = uVar15 - 1;
          } while (bVar27);
          local_13c = 0;
LAB_008064ec:
          FUN_006d3154(auStack_30,iVar12);
          FUN_006d35d4(local_90,auStack_30,0);
          FUN_00707778(auStack_30);
          if (iVar21 < iVar21 + iVar23) {
            iVar4 = iVar21;
            do {
              if (iVar18 < iVar18 + local_118) {
                pbVar17 = (byte *)(local_90[0] + iVar4 * local_88 + local_84 * iVar18);
                iVar13 = iVar18;
                do {
                  pbVar1 = pbVar17 + 1;
                  pbVar2 = pbVar17 + 2;
                  bVar3 = *pbVar17;
                  pbVar17 = pbVar17 + local_84;
                  (**(code **)(*(int *)(iVar12 + 0x2c) + 0x4c))
                            (*(int *)(iVar12 + 0x2c),iVar13,iVar4,
                             uVar24 & ((uint)*pbVar1 << (local_148 & 0xff)) >> (local_144 & 0xff) |
                             uVar22 & ((uint)*pbVar2 << (local_150 & 0xff)) >> (local_14c & 0xff) |
                             uVar19 & ((uint)bVar3 << (local_140 & 0xff)) >> (local_13c & 0xff));
                  iVar13 = iVar13 + 1;
                } while (iVar13 != iVar18 + local_118);
              }
              iVar4 = iVar4 + 1;
            } while (iVar4 != iVar21 + iVar23);
          }
          FUN_006d3654(local_90);
          iVar4 = *(int *)(iVar12 + 0x48);
        }
        XPutImage(DAT_00f6e684,uVar11,iVar4,*(undefined4 *)(iVar12 + 0x2c),iVar18,iVar21,iVar9,
                  local_130,local_118,iVar23);
        FUN_00697eec(auStack_2c);
        local_130 = iVar14 + local_130;
        iVar18 = piVar8[1] + piVar8[3];
        if (iVar18 <= local_130) break;
        local_118 = piVar8[2];
      } while( true );
    }
  }
  free(local_50);
LAB_00806724:
  uVar11 = FUN_00639acc();
  *(undefined4 *)(param_1 + 0x1c) = uVar11;
  FUN_0069bf5c(param_1,10);
  free(local_60);
  return;
}

