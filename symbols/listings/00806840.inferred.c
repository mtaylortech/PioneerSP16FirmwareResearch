/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int * candidate_00806840(int param_1)

{
  byte *pbVar1;
  byte *pbVar2;
  byte bVar3;
  int iVar4;
  int iVar5;
  undefined4 *puVar6;
  void *pvVar7;
  uint *puVar8;
  int *extraout_r0;
  int *piVar9;
  int iVar10;
  uint uVar11;
  undefined4 uVar12;
  int *piVar13;
  int iVar14;
  int iVar15;
  int iVar16;
  uint uVar17;
  byte *pbVar18;
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
  uint uStack_150;
  uint uStack_14c;
  uint uStack_148;
  uint uStack_144;
  uint uStack_140;
  uint uStack_13c;
  int iStack_130;
  int iStack_120;
  int iStack_11c;
  int iStack_118;
  undefined4 uStack_ec;
  undefined4 uStack_e8;
  int iStack_e4;
  int iStack_e0;
  int iStack_a8;
  int iStack_9c;
  int aiStack_90 [2];
  int iStack_88;
  int iStack_84;
  int iStack_70;
  int iStack_6c;
  undefined8 uStack_68;
  int *piStack_60;
  undefined4 uStack_5c;
  int iStack_58;
  int *piStack_50;
  int iStack_4c;
  int iStack_48;
  undefined8 uStack_40;
  undefined1 auStack_38 [4];
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [12];
  
  if (*(int *)(param_1 + 0x28) == 0) {
    piVar9 = (int *)FUN_00639acc();
    if ((int *)(*(int *)(param_1 + 0x1c) + 3000U) < piVar9) {
      FUN_00697918(param_1);
      piVar9 = (int *)(param_1 + 0x18);
      iVar15 = *_UNK_00806894;
      iVar4 = *piVar9;
      if (iVar15 != iVar4) {
        if (iVar15 != 0) {
          piVar13 = (int *)(iVar15 + 4);
          DataMemoryBarrier(0xf);
          do {
            bVar27 = (bool)hasExclusiveAccess(piVar13);
          } while (!bVar27);
          *piVar13 = *piVar13 + 1;
          DataMemoryBarrier(0xf);
          iVar4 = *piVar9;
        }
        *piVar9 = iVar15;
        FUN_0071da04(iVar4);
      }
      return piVar9;
    }
    return piVar9;
  }
  FUN_00697918();
  piStack_60 = (int *)0x0;
  uStack_5c = 0;
  iStack_58 = 0;
  FUN_004ff510(param_1 + 0x20,&piStack_60);
  if (iStack_58 < 2) {
    if (iStack_58 == 0) goto LAB_00806724;
    iStack_120 = *piStack_60;
    iVar4 = piStack_60[2];
    iVar15 = piStack_60[3];
    iStack_11c = piStack_60[1];
  }
  else {
    iStack_120 = *piStack_60;
    iStack_11c = piStack_60[1];
    iVar4 = iStack_120 + piStack_60[2];
    iVar5 = iStack_58 << 4;
    iVar14 = iStack_58;
    iVar15 = iStack_11c + piStack_60[3];
    while( true ) {
      iVar14 = iVar14 + -1;
      iVar10 = iVar5 + -0x10;
      if (iVar14 == 0) break;
      iVar21 = *(int *)((int)piStack_60 + iVar10);
      iVar23 = *(int *)((int)piStack_60 + iVar5 + -0xc);
      if (iVar21 <= iStack_120) {
        iStack_120 = iVar21;
      }
      if (iVar23 <= iStack_11c) {
        iStack_11c = iVar23;
      }
      iVar21 = iVar21 + *(int *)((int)piStack_60 + iVar5 + -8);
      iVar23 = iVar23 + *(int *)((int)piStack_60 + iVar5 + -4);
      if (iVar4 < iVar21) {
        iVar4 = iVar21;
      }
      iVar5 = iVar10;
      if (iVar15 < iVar23) {
        iVar15 = iVar23;
      }
    }
    iVar4 = iVar4 - iStack_120;
    iVar15 = iVar15 - iStack_11c;
  }
  if ((iVar4 < 1) || (iVar15 < 1)) goto LAB_00806724;
  if (*(int *)(param_1 + 0x18) == 0) {
LAB_00805f34:
    puVar6 = operator_new(0x4c);
    uVar17 = iVar4 + 0x1fU & 0xffffffe0;
    uVar19 = iVar15 + 0x1fU & 0xffffffe0;
    uVar20 = *(undefined4 *)(*(int *)(param_1 + 0x14) + 0x5c);
    iVar5 = *(int *)(*(int *)(param_1 + 0x14) + 0x58);
    FUN_006d2f0c(puVar6,1,uVar17,uVar19);
    uVar12 = DAT_00806838;
    puVar6[0xd] = 0;
    puVar6[0xe] = 0;
    puVar6[0x12] = 0;
    *puVar6 = uVar12;
    puVar6[0xc] = uVar20;
    puVar6[0xf] = 3;
    puVar6[0x10] = uVar17 * 3;
    FUN_00697ecc(auStack_2c);
    iVar4 = puVar6[0x10];
    free((void *)puVar6[0xd]);
    pvVar7 = malloc(iVar4 * uVar19);
    puVar6[0xd] = pvVar7;
    puVar6[0x11] = pvVar7;
    puVar8 = calloc(1,0x58);
    iVar14 = puVar6[0xc];
    iVar4 = puVar6[0xf];
    iVar15 = *DAT_0080683c;
    uVar22 = puVar6[0x10];
    uVar11 = *(uint *)(iVar15 + 0x30);
    uVar24 = *(uint *)(iVar15 + 0x34);
    uVar26 = *(uint *)(iVar15 + 0x3c);
    puVar6[0xb] = puVar8;
    puVar8[2] = 0;
    *puVar8 = uVar17;
    puVar8[1] = uVar19;
    puVar8[3] = 2;
    puVar8[4] = (uint)pvVar7;
    puVar8[8] = 0x20;
    puVar8[5] = uVar11;
    puVar8[0xc] = 0xff0000;
    puVar8[6] = uVar24;
    puVar8[0xd] = 0xff00;
    puVar8[7] = uVar26;
    puVar8[9] = iVar4 << 3;
    puVar8[10] = uVar22;
    puVar8[0xb] = iVar4 << 3;
    puVar8[0xe] = 0xff;
    if (iVar14 == 0x10) {
      free((void *)puVar6[0xe]);
      pvVar7 = malloc(uVar17 * 2 * uVar19);
      uVar25 = *(undefined4 *)(iVar5 + 0xc);
      uVar12 = *(undefined4 *)(iVar5 + 0x10);
      uVar20 = *(undefined4 *)(iVar5 + 0x14);
      iVar4 = puVar6[0xb];
      puVar6[0xe] = pvVar7;
      *(void **)(iVar4 + 0x10) = pvVar7;
      *(undefined4 *)(iVar4 + 0x20) = 0x10;
      *(undefined4 *)(iVar4 + 0x24) = 0x10;
      *(uint *)(iVar4 + 0x28) = uVar17 * 2;
      *(undefined4 *)(iVar4 + 0x2c) = 0x10;
      *(undefined4 *)(iVar4 + 0x30) = uVar25;
      *(undefined4 *)(iVar4 + 0x34) = uVar12;
      *(undefined4 *)(iVar4 + 0x38) = uVar20;
    }
    XInitImage();
    FUN_00697eec(auStack_2c);
    FUN_006d3154(auStack_38,puVar6);
    FUN_006d3310(param_1 + 0x18,auStack_38);
    FUN_00707778(auStack_38);
  }
  else {
    iVar5 = FUN_006d3360(param_1 + 0x18);
    if ((iVar5 < iVar4) || (iVar5 = FUN_006d3370(param_1 + 0x18), iVar5 < iVar15))
    goto LAB_00805f34;
  }
  FUN_0069bf5c(param_1,10);
  iVar4 = iStack_58;
  iVar15 = 0;
  piStack_50 = (int *)0x0;
  iStack_4c = 0;
  iStack_48 = iStack_58;
  if (iStack_58 == 0) {
    __size = 0;
  }
  else {
    __size = iStack_58 << 4;
    if (iStack_58 < 1) {
      iStack_4c = iStack_58;
    }
    else {
      piStack_50 = malloc(__size);
      iStack_4c = iVar4;
      piVar9 = piStack_50;
      do {
        if (piVar9 != (int *)0x0) {
          *piVar9 = piStack_60[iVar15 * 4];
          piVar9[1] = piStack_60[iVar15 * 4 + 1];
          piVar9[2] = piStack_60[iVar15 * 4 + 2];
          piVar9[3] = piStack_60[iVar15 * 4 + 3];
        }
        iVar15 = iVar15 + 1;
        piVar9 = piVar9 + 4;
      } while (iVar15 != iVar4);
    }
  }
  for (piVar9 = piStack_50; (int *)((int)piStack_50 + __size) != piVar9; piVar9 = piVar9 + 4) {
    *piVar9 = *piVar9 - iStack_120;
    piVar9[1] = piVar9[1] - iStack_11c;
  }
  iVar4 = *(int *)(param_1 + 0x14);
  if ((*(int *)(iVar4 + 0x5c) == 0x20) &&
     (piVar13 = (int *)((int)piStack_60 + __size), piVar9 = piStack_60, piStack_60 != piVar13)) {
    do {
      uStack_68 = *(undefined8 *)(piVar9 + 2);
      iStack_6c = piVar9[1] - iStack_11c;
      iStack_70 = *piVar9 - iStack_120;
      FUN_006c16fc(auStack_34,0);
      FUN_0070a3b8(param_1 + 0x18,&iStack_70,auStack_34);
      piVar9 = piVar9 + 4;
      FUN_006a0280(auStack_34);
    } while (piVar9 != piVar13);
    iVar4 = *(int *)(param_1 + 0x14);
  }
  piVar9 = (int *)FUN_007ac33c(*(undefined4 *)(iVar4 + 4));
  uStack_40 = FloatVectorNeg(CONCAT44(iStack_11c,iStack_120),1,4);
  piVar9 = (int *)(**(code **)(*piVar9 + 0x2c))(piVar9,param_1 + 0x18,&uStack_40,&piStack_50);
  FUN_00789bc0(*(undefined4 *)(param_1 + 0x14),piVar9);
  if (piVar9 != (int *)0x0) {
    (**(code **)(*piVar9 + 4))(piVar9);
  }
  piVar13 = piStack_60 + iStack_58 * 4;
  for (piVar9 = piStack_60; piVar9 != piVar13; piVar9 = piVar9 + 4) {
    iStack_118 = piVar9[2];
    iVar4 = __aeabi_idiv(0xc80,iStack_118);
    iStack_130 = piVar9[1];
    iVar15 = iStack_130 + piVar9[3];
    if (iVar4 < 1) {
      iVar4 = 1;
    }
    if (iStack_130 < iVar15) {
      do {
        iVar10 = *piVar9;
        iVar14 = *(int *)(param_1 + 0x18);
        uVar12 = *(undefined4 *)(*(int *)(param_1 + 0x14) + 0x38);
        FUN_00697ecc(auStack_2c);
        iVar5 = *(int *)(iVar14 + 0x48);
        if (iVar5 == 0) {
          uStack_ec = 3;
          uStack_e8 = 0xffffffff;
          iStack_e4 = iVar5;
          iStack_e0 = iVar5;
          iStack_a8 = iVar5;
          iStack_9c = iVar5;
          iVar5 = XCreateGC(DAT_00f6e684,uVar12,0x9000f,&uStack_ec);
          *(int *)(iVar14 + 0x48) = iVar5;
        }
        iVar23 = iVar4;
        if (iVar15 - iStack_130 <= iVar4) {
          iVar23 = iVar15 - iStack_130;
        }
        iVar15 = iVar10 - iStack_120;
        iVar21 = iStack_130 - iStack_11c;
        if (*(int *)(iVar14 + 0x30) == 0x10) {
          iVar5 = *(int *)(iVar14 + 0x2c);
          uVar22 = *(uint *)(iVar5 + 0x30);
          uVar19 = *(uint *)(iVar5 + 0x38);
          uVar24 = *(uint *)(iVar5 + 0x34);
          uVar11 = 0x20;
          uVar17 = 0x1f;
          do {
            if ((uVar22 >> (uVar17 & 0xff) & 1) != 0) {
              uStack_150 = uVar11 - 8 & ~((int)(uVar11 - 8) >> 0x1f);
              goto LAB_008063d0;
            }
            bVar27 = uVar17 != 0;
            uVar11 = uVar17;
            uVar17 = uVar17 - 1;
          } while (bVar27);
          uStack_150 = 0;
LAB_008063d0:
          uVar11 = 0x20;
          uVar17 = 0x1f;
          do {
            if ((uVar22 >> (uVar17 & 0xff) & 1) != 0) {
              uStack_14c = 8 - uVar11 & ~((int)(8 - uVar11) >> 0x1f);
              goto LAB_0080640c;
            }
            bVar27 = uVar17 != 0;
            uVar11 = uVar17;
            uVar17 = uVar17 - 1;
          } while (bVar27);
          uStack_14c = 0;
LAB_0080640c:
          uVar11 = 0x20;
          uVar17 = 0x1f;
          do {
            if ((uVar24 >> (uVar17 & 0xff) & 1) != 0) {
              uStack_148 = uVar11 - 8 & ~((int)(uVar11 - 8) >> 0x1f);
              goto LAB_00806444;
            }
            bVar27 = uVar17 != 0;
            uVar11 = uVar17;
            uVar17 = uVar17 - 1;
          } while (bVar27);
          uStack_148 = 0;
LAB_00806444:
          uVar11 = 0x20;
          uVar17 = 0x1f;
          do {
            if ((uVar24 >> (uVar17 & 0xff) & 1) != 0) {
              uStack_144 = 8 - uVar11 & ~((int)(8 - uVar11) >> 0x1f);
              goto LAB_0080647c;
            }
            bVar27 = uVar17 != 0;
            uVar11 = uVar17;
            uVar17 = uVar17 - 1;
          } while (bVar27);
          uStack_144 = 0;
LAB_0080647c:
          uVar11 = 0x20;
          uVar17 = 0x1f;
          do {
            if ((uVar19 >> (uVar17 & 0xff) & 1) != 0) {
              uStack_140 = uVar11 - 8 & ~((int)(uVar11 - 8) >> 0x1f);
              goto LAB_008064b4;
            }
            bVar27 = uVar17 != 0;
            uVar11 = uVar17;
            uVar17 = uVar17 - 1;
          } while (bVar27);
          uStack_140 = 0;
LAB_008064b4:
          uVar11 = 0x20;
          uVar17 = 0x1f;
          do {
            if ((uVar19 >> (uVar17 & 0xff) & 1) != 0) {
              uStack_13c = 8 - uVar11 & ~((int)(8 - uVar11) >> 0x1f);
              goto LAB_008064ec;
            }
            bVar27 = uVar17 != 0;
            uVar11 = uVar17;
            uVar17 = uVar17 - 1;
          } while (bVar27);
          uStack_13c = 0;
LAB_008064ec:
          FUN_006d3154(auStack_30,iVar14);
          FUN_006d35d4(aiStack_90,auStack_30,0);
          FUN_00707778(auStack_30);
          if (iVar21 < iVar21 + iVar23) {
            iVar5 = iVar21;
            do {
              if (iVar15 < iVar15 + iStack_118) {
                pbVar18 = (byte *)(aiStack_90[0] + iVar5 * iStack_88 + iStack_84 * iVar15);
                iVar16 = iVar15;
                do {
                  pbVar1 = pbVar18 + 1;
                  pbVar2 = pbVar18 + 2;
                  bVar3 = *pbVar18;
                  pbVar18 = pbVar18 + iStack_84;
                  (**(code **)(*(int *)(iVar14 + 0x2c) + 0x4c))
                            (*(int *)(iVar14 + 0x2c),iVar16,iVar5,
                             uVar24 & ((uint)*pbVar1 << (uStack_148 & 0xff)) >> (uStack_144 & 0xff)
                             | uVar22 & ((uint)*pbVar2 << (uStack_150 & 0xff)) >>
                                        (uStack_14c & 0xff) |
                             uVar19 & ((uint)bVar3 << (uStack_140 & 0xff)) >> (uStack_13c & 0xff));
                  iVar16 = iVar16 + 1;
                } while (iVar16 != iVar15 + iStack_118);
              }
              iVar5 = iVar5 + 1;
            } while (iVar5 != iVar21 + iVar23);
          }
          FUN_006d3654(aiStack_90);
          iVar5 = *(int *)(iVar14 + 0x48);
        }
        XPutImage(DAT_00f6e684,uVar12,iVar5,*(undefined4 *)(iVar14 + 0x2c),iVar15,iVar21,iVar10,
                  iStack_130,iStack_118,iVar23);
        FUN_00697eec(auStack_2c);
        iStack_130 = iVar4 + iStack_130;
        iVar15 = piVar9[1] + piVar9[3];
        if (iVar15 <= iStack_130) break;
        iStack_118 = piVar9[2];
      } while( true );
    }
  }
  free(piStack_50);
LAB_00806724:
  uVar12 = FUN_00639acc();
  *(undefined4 *)(param_1 + 0x1c) = uVar12;
  FUN_0069bf5c(param_1,10);
  free(piStack_60);
  return extraout_r0;
}

